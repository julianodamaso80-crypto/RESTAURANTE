import json

import structlog
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from connectors.ifood.models import RawEvent, RawEventStatus

from .models import NinetyNineStoreCredential
from .signature import verify_signature
from .tasks import process_ninetynine_event

log = structlog.get_logger()


@csrf_exempt
@require_POST
def ninetynine_webhook(request):
    """99Food webhook endpoint.

    Mandatory pipeline (identical to iFood):
    - Respond 202 in < 2 seconds
    - Validate signature before anything else
    - Persist RawEvent before responding
    - No heavy synchronous work
    """
    payload_bytes = request.body
    signature = request.headers.get("X-Ninetynine-Signature", "")

    try:
        payload = json.loads(payload_bytes)
    except (json.JSONDecodeError, ValueError):
        log.warning("99food_webhook_invalid_json")
        return JsonResponse({"detail": "invalid json"}, status=400)

    # Open Delivery Protocol — standard fields
    event_id = payload.get("id", "") or payload.get("eventId", "")
    merchant_id = payload.get("merchantId", "")
    event_type = payload.get("code", "") or payload.get("type", "")

    webhook_secret = _get_webhook_secret(merchant_id)

    if not verify_signature(payload_bytes, signature, webhook_secret):
        log.warning("99food_webhook_unauthorized", merchant_id=merchant_id, event_id=event_id)
        return JsonResponse({"detail": "unauthorized"}, status=401)

    # Persist with source='99food' — reuses RawEvent from iFood
    raw_event = RawEvent.objects.create(
        source="99food",
        event_id=event_id,
        event_type=event_type,
        payload=payload,
        headers={
            "x-ninetynine-signature": signature[:16] + "..." if signature else "",
            "content-type": request.content_type,
        },
        status=RawEventStatus.RECEIVED,
    )

    log.info(
        "99food_webhook_received",
        event_id=event_id,
        event_type=event_type,
        raw_event_id=str(raw_event.id),
    )

    process_ninetynine_event.delay(str(raw_event.id))

    raw_event.status = RawEventStatus.ENQUEUED
    raw_event.save(update_fields=["status"])

    return JsonResponse({"received": True}, status=202)


@require_GET
def ninetynine_health(request):
    """99Food connector status."""
    from datetime import timedelta

    from django.db.models import Count
    from django.utils import timezone

    active_creds = NinetyNineStoreCredential.objects.filter(is_active=True).count()

    last_hour = timezone.now() - timedelta(hours=1)
    recent_events = (
        RawEvent.objects.filter(source="99food", received_at__gte=last_hour)
        .values("status")
        .annotate(count=Count("id"))
    )

    events_by_status = {row["status"]: row["count"] for row in recent_events}

    return JsonResponse({
        "connector": "99food",
        "status": "ok" if active_creds > 0 else "no_stores_configured",
        "active_stores": active_creds,
        "events_last_hour": events_by_status,
    })


def _get_webhook_secret(merchant_id: str) -> str:
    from django.conf import settings

    global_secret = getattr(settings, "NINETYNINE_WEBHOOK_SECRET", "")

    if not merchant_id:
        return global_secret

    try:
        cred = (
            NinetyNineStoreCredential.objects.filter(merchant_id=merchant_id, is_active=True)
            .only("webhook_secret")
            .first()
        )
        return cred.webhook_secret if cred and cred.webhook_secret else global_secret
    except Exception:
        return global_secret
