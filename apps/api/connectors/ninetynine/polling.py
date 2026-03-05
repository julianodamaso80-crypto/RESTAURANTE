"""99Food order polling via Celery.

Per-store polling: after manual connection (AppShopID), starts polling
for that specific store every 30 seconds.

Same pipeline as iFood polling (ADR-022) — converges at RawEvent + process_ninetynine_event.
"""

from datetime import timedelta

import requests
import structlog
import structlog.contextvars
from celery import shared_task
from django.conf import settings
from django.utils import timezone

log = structlog.get_logger()

NINETYNINE_API_BASE = getattr(
    settings,
    "NINETYNINE_API_BASE_URL",
    "https://openapi.didi-food.com/v4/opendelivery",
)


@shared_task(bind=True)
def start_polling_for_ninetynine_store(self, store_id: str):
    """Start 99Food polling for a store. Called after connection."""
    log.info("99food_polling_started", store_id=store_id)
    poll_ninetynine_store.delay(store_id)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def poll_ninetynine_store(self, store_id: str):
    """Poll 99Food via Open Delivery Protocol.

    Pipeline:
    1. Fetch token for store
    2. GET /order/v1.0/events:polling
    3. Same pipeline as webhook (RawEvent -> Celery -> Order)
    4. POST acknowledgment
    5. Schedule next poll in 30s
    """
    from connectors.ifood.models import RawEvent, RawEventStatus
    from connectors.ninetynine.models import NinetyNineStoreCredential
    from connectors.ninetynine.oauth import NinetyNineAuthClient, NinetyNineAuthError
    from connectors.ninetynine.tasks import process_ninetynine_event
    from tenants.models import Store

    structlog.contextvars.bind_contextvars(store_id=store_id, task="poll_99food")

    try:
        store = Store.objects.get(id=store_id)
        cred = NinetyNineStoreCredential.objects.get(store=store, is_active=True)
    except (Store.DoesNotExist, NinetyNineStoreCredential.DoesNotExist):
        log.warning("99food_polling_store_not_found", store_id=store_id)
        return

    # Renew token if expiring soon (< 30 min)
    if cred.token_expires_at:
        time_left = cred.token_expires_at - timezone.now()
        if time_left < timedelta(minutes=30):
            try:
                client = NinetyNineAuthClient(app_shop_id=cred.client_id)
                token_data = client.get_token()
                expires_in = token_data.get("expires_in", 21600)
                cred.access_token = token_data["access_token"]
                cred.token_expires_at = timezone.now() + timedelta(seconds=expires_in)
                cred.save(update_fields=["access_token", "token_expires_at"])
                log.info("99food_token_refreshed", store_id=store_id)
            except NinetyNineAuthError as exc:
                log.error("99food_token_refresh_failed", error=str(exc))
                cred.is_active = False
                cred.save(update_fields=["is_active"])
                return

    # Fetch events
    try:
        response = requests.get(
            f"{NINETYNINE_API_BASE}/order/v1.0/events:polling",
            headers={
                "Authorization": f"Bearer {cred.access_token}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )

        if response.status_code == 204:
            log.debug("99food_polling_no_events", store_id=store_id)
            poll_ninetynine_store.apply_async(args=[store_id], countdown=30)
            return

        if response.status_code == 401:
            log.warning("99food_polling_unauthorized", store_id=store_id)
            try:
                client = NinetyNineAuthClient(app_shop_id=cred.client_id)
                token_data = client.get_token()
                cred.access_token = token_data["access_token"]
                cred.save(update_fields=["access_token"])
            except NinetyNineAuthError:
                pass
            poll_ninetynine_store.apply_async(args=[store_id], countdown=5)
            return

        if response.status_code != 200:
            log.error(
                "99food_polling_error",
                status=response.status_code,
                store_id=store_id,
            )
            poll_ninetynine_store.apply_async(args=[store_id], countdown=60)
            return

        events = response.json()
        log.info(
            "99food_polling_events_received",
            count=len(events),
            store_id=store_id,
        )

        event_ids_to_ack = []

        for event in events:
            event_id = event.get("id") or event.get("orderId", "")
            event_type = event.get("code", "") or event.get("fullCode", "")
            order_id = event.get("orderId", "")

            event_ids_to_ack.append({"id": event_id})

            # Idempotency
            if RawEvent.objects.filter(event_id=event_id, source="99food").exists():
                log.debug("99food_polling_duplicate", event_id=event_id)
                continue

            # Persist RawEvent — same model as iFood with source='99food'
            raw_event = RawEvent.objects.create(
                source="99food",
                event_id=event_id,
                event_type=event_type,
                payload={
                    "id": event_id,
                    "code": event_type,
                    "orderId": order_id,
                    "merchantId": cred.merchant_id,
                    "origin": "polling",
                },
                status=RawEventStatus.RECEIVED,
            )

            # Process via existing pipeline from PR 11
            process_ninetynine_event.delay(str(raw_event.id))

            raw_event.status = RawEventStatus.ENQUEUED
            raw_event.save(update_fields=["status"])

        # Acknowledgment
        if event_ids_to_ack:
            try:
                requests.post(
                    f"{NINETYNINE_API_BASE}/order/v1.0/events/acknowledgment",
                    headers={
                        "Authorization": f"Bearer {cred.access_token}",
                        "Content-Type": "application/json",
                    },
                    json=event_ids_to_ack,
                    timeout=10,
                )
            except Exception as exc:
                log.error("99food_ack_error", error=str(exc))

        # Next poll in 30s
        poll_ninetynine_store.apply_async(args=[store_id], countdown=30)

    except requests.RequestException as exc:
        log.error(
            "99food_polling_network_error",
            error=str(exc),
            store_id=store_id,
        )
        poll_ninetynine_store.apply_async(args=[store_id], countdown=60)
