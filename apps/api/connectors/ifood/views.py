import json

import structlog
from django.db import models
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import IFoodStoreCredential, RawEvent, RawEventStatus
from .signature import verify_signature
from .tasks import process_ifood_event

log = structlog.get_logger()


@csrf_exempt
@require_POST
def ifood_webhook(request):
    """iFood webhook endpoint.

    Mandatory certification rules:
    - Respond 202 in < 2 seconds
    - Validate X-IFood-Signature before anything
    - No heavy synchronous work
    - Persist raw event before responding
    """
    # 1. Read raw payload (needed for signature validation)
    payload_bytes = request.body
    signature = request.headers.get("X-Ifood-Signature", "")

    # 2. Minimal parse to extract event_id and merchant_id
    try:
        payload = json.loads(payload_bytes)
    except (json.JSONDecodeError, ValueError):
        log.warning("ifood_webhook_invalid_json")
        return JsonResponse({"detail": "invalid json"}, status=400)

    event_id = payload.get("id", "") or payload.get("eventId", "")
    merchant_id = payload.get("merchantId", "") or payload.get("correlationId", "")
    event_type = payload.get("code", "") or payload.get("type", "")

    # 3. Get credential for signature validation
    webhook_secret = _get_webhook_secret(merchant_id)

    # 4. Validate signature — 401 if invalid
    if not verify_signature(payload_bytes, signature, webhook_secret):
        log.warning("ifood_webhook_unauthorized", merchant_id=merchant_id, event_id=event_id)
        return JsonResponse({"detail": "unauthorized"}, status=401)

    # 5. Persist raw event — BEFORE responding 202
    raw_event = RawEvent.objects.create(
        source="ifood",
        event_id=event_id,
        event_type=event_type,
        payload=payload,
        headers={
            "x-ifood-signature": signature[:16] + "..." if signature else "",
            "content-type": request.content_type,
        },
        status=RawEventStatus.RECEIVED,
    )

    log.info(
        "ifood_webhook_received",
        event_id=event_id,
        event_type=event_type,
        raw_event_id=str(raw_event.id),
    )

    # 6. Enqueue — async, does not block
    process_ifood_event.delay(str(raw_event.id))

    raw_event.status = RawEventStatus.ENQUEUED
    raw_event.save(update_fields=["status"])

    # 7. Respond 202 immediately
    return JsonResponse({"received": True}, status=202)


def _get_webhook_secret(merchant_id: str) -> str:
    """Get the webhook secret for a store by iFood merchant_id.

    Returns empty string if not found (signature will fail — intentional).
    """
    from django.conf import settings

    global_secret = getattr(settings, "IFOOD_WEBHOOK_SECRET", "")

    if not merchant_id:
        return global_secret

    try:
        cred = (
            IFoodStoreCredential.objects.filter(merchant_id=merchant_id, is_active=True)
            .only("webhook_secret")
            .first()
        )
        return cred.webhook_secret if cred and cred.webhook_secret else global_secret
    except Exception:
        return global_secret


@require_GET
def ifood_health(request):
    """iFood connector status: configured/active stores and recent event counts."""
    from datetime import timedelta

    active_creds = IFoodStoreCredential.objects.filter(is_active=True).count()

    last_hour = timezone.now() - timedelta(hours=1)
    recent_events = (
        RawEvent.objects.filter(source="ifood", received_at__gte=last_hour)
        .values("status")
        .annotate(count=models.Count("id"))
    )

    events_by_status = {row["status"]: row["count"] for row in recent_events}

    return JsonResponse(
        {
            "connector": "ifood",
            "status": "ok" if active_creds > 0 else "no_stores_configured",
            "active_stores": active_creds,
            "events_last_hour": events_by_status,
        }
    )
