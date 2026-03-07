import json

import structlog
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from connectors.ifood.models import RawEvent, RawEventStatus

from .models import RappiStoreCredential
from .tasks import process_rappi_event

log = structlog.get_logger()


@csrf_exempt
@require_POST
def rappi_webhook(request):
    """Rappi webhook endpoint.

    Receives NEW_ORDER and ORDER_STATUS_CHANGED events.
    Pipeline: persist RawEvent -> respond 202 -> enqueue async processing.
    """
    payload_bytes = request.body

    try:
        payload = json.loads(payload_bytes)
    except (json.JSONDecodeError, ValueError):
        log.warning("rappi_webhook_invalid_json")
        return JsonResponse({"detail": "invalid json"}, status=400)

    event_id = payload.get("id", "") or payload.get("eventId", "")
    event_type = payload.get("event", "") or payload.get("type", "")
    rappi_store_id = payload.get("store_id", "") or payload.get("storeId", "")

    # Validate webhook secret if configured
    webhook_secret = _get_webhook_secret(rappi_store_id)
    incoming_secret = request.headers.get("X-Rappi-Secret", "")
    if webhook_secret and incoming_secret != webhook_secret:
        log.warning("rappi_webhook_unauthorized", rappi_store_id=rappi_store_id, event_id=event_id)
        return JsonResponse({"detail": "unauthorized"}, status=401)

    raw_event = RawEvent.objects.create(
        source="rappi",
        event_id=event_id,
        event_type=event_type,
        payload=payload,
        headers={
            "x-rappi-secret": incoming_secret[:16] + "..." if incoming_secret else "",
            "content-type": request.content_type,
        },
        status=RawEventStatus.RECEIVED,
    )

    log.info(
        "rappi_webhook_received",
        event_id=event_id,
        event_type=event_type,
        raw_event_id=str(raw_event.id),
    )

    process_rappi_event.delay(str(raw_event.id))

    raw_event.status = RawEventStatus.ENQUEUED
    raw_event.save(update_fields=["status"])

    return JsonResponse({"received": True}, status=202)


@require_GET
def rappi_health(request):
    """Rappi connector status."""
    from datetime import timedelta

    from django.db.models import Count
    from django.utils import timezone

    active_creds = RappiStoreCredential.objects.filter(is_active=True).count()

    last_hour = timezone.now() - timedelta(hours=1)
    recent_events = (
        RawEvent.objects.filter(source="rappi", received_at__gte=last_hour)
        .values("status")
        .annotate(count=Count("id"))
    )

    events_by_status = {row["status"]: row["count"] for row in recent_events}

    return JsonResponse({
        "connector": "rappi",
        "status": "ok" if active_creds > 0 else "no_stores_configured",
        "active_stores": active_creds,
        "events_last_hour": events_by_status,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def rappi_configure(request):
    """Save Rappi token and store_id for a store."""
    store_id = request.data.get("store_id") or request.headers.get("X-Store-Id")
    rappi_token = request.data.get("rappi_token", "").strip()
    rappi_store_id = request.data.get("rappi_store_id", "").strip()
    environment = request.data.get("environment", "prod")

    if not store_id or not rappi_token or not rappi_store_id:
        return Response({"error": "store_id, rappi_token, and rappi_store_id are required"}, status=400)

    from tenants.models import Store

    try:
        store = Store.objects.get(id=store_id)
    except Store.DoesNotExist:
        return Response({"error": "Store not found"}, status=404)

    cred, created = RappiStoreCredential.objects.update_or_create(
        store=store,
        defaults={
            "rappi_token": rappi_token,
            "rappi_store_id": rappi_store_id,
            "environment": environment,
            "is_active": True,
        },
    )

    # Verify connection
    from .client import RappiAPIClient

    client = RappiAPIClient(rappi_token=cred.rappi_token, base_url=cred.base_url)
    connected = client.check_connection()

    return Response({
        "status": "connected" if connected else "token_invalid",
        "rappi_store_id": cred.rappi_store_id,
        "created": created,
    }, status=201 if created else 200)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def rappi_status(request):
    """Check Rappi connection status for a store."""
    store_id = request.query_params.get("store_id") or request.headers.get("X-Store-Id")

    if not store_id:
        return Response({"error": "store_id is required"}, status=400)

    try:
        cred = RappiStoreCredential.objects.get(store_id=store_id, is_active=True)
    except RappiStoreCredential.DoesNotExist:
        return Response({"status": "not_configured"})

    from .client import RappiAPIClient

    client = RappiAPIClient(rappi_token=cred.rappi_token, base_url=cred.base_url)
    connected = client.check_connection()

    return Response({
        "status": "connected" if connected else "disconnected",
        "rappi_store_id": cred.rappi_store_id,
        "environment": cred.environment,
    })


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def rappi_disconnect(request):
    """Remove Rappi credential for a store."""
    store_id = request.data.get("store_id") or request.headers.get("X-Store-Id")

    if not store_id:
        return Response({"error": "store_id is required"}, status=400)

    deleted, _ = RappiStoreCredential.objects.filter(store_id=store_id).delete()

    if deleted:
        return Response({"status": "disconnected"})
    return Response({"status": "not_configured"})


def _get_webhook_secret(rappi_store_id: str) -> str:
    from django.conf import settings

    global_secret = getattr(settings, "RAPPI_WEBHOOK_SECRET", "")

    if not rappi_store_id:
        return global_secret

    try:
        cred = (
            RappiStoreCredential.objects.filter(rappi_store_id=rappi_store_id, is_active=True)
            .only("webhook_secret")
            .first()
        )
        return cred.webhook_secret if cred and cred.webhook_secret else global_secret
    except Exception:
        return global_secret
