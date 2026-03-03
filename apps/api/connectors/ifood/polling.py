"""iFood order polling via Celery Beat.

Alternative to webhook: actively polls iFood's events:polling endpoint
every N seconds for each active store credential.

ADR-022: Polling is additive to webhook — both paths converge at RawEvent + process_ifood_event.
"""

import structlog
from celery import shared_task

from .client import IFoodAPIClient, IFoodAPIError

log = structlog.get_logger()


@shared_task(bind=True, max_retries=0)
def poll_ifood_orders(self):
    """Poll iFood events for all active store credentials.

    For each active IFoodStoreCredential:
    1. Call poll_events() to get pending events
    2. For each event, create RawEvent if not already exists (idempotency by event_id)
    3. Enqueue process_ifood_event for each NEW RawEvent
    4. Acknowledge all fetched events with iFood

    Designed for Celery Beat — runs every 30 seconds.
    Each store is polled independently: one store's failure does NOT block others.
    max_retries=0: polling failures are logged and retried on next beat cycle.
    """
    from .models import IFoodStoreCredential, RawEvent, RawEventStatus
    from .tasks import process_ifood_event

    active_credentials = (
        IFoodStoreCredential.objects.filter(is_active=True)
        .exclude(access_token="")
        .select_related("store__company__tenant")
    )

    total_new_events = 0
    total_stores_polled = 0

    for cred in active_credentials:
        try:
            new_events = _poll_single_store(cred, RawEvent, RawEventStatus, process_ifood_event)
            total_new_events += new_events
            total_stores_polled += 1
        except Exception:
            log.exception(
                "ifood_poll_store_failed",
                store_id=str(cred.store_id),
                merchant_id=cred.merchant_id,
            )

    log.info(
        "ifood_poll_cycle_complete",
        stores_polled=total_stores_polled,
        new_events=total_new_events,
    )

    return {"stores_polled": total_stores_polled, "new_events": total_new_events}


def _poll_single_store(cred, RawEvent, RawEventStatus, process_ifood_event) -> int:
    """Poll a single store and return count of new events created."""
    client = IFoodAPIClient(access_token=cred.access_token)

    try:
        events = client.poll_events(merchant_id=cred.merchant_id)
    except IFoodAPIError as exc:
        log.warning(
            "ifood_poll_api_error",
            store_id=str(cred.store_id),
            merchant_id=cred.merchant_id,
            error=str(exc),
        )
        return 0

    if not events:
        return 0

    new_count = 0
    event_ids_to_ack = []

    for event_data in events:
        event_id = event_data.get("id", "") or event_data.get("eventId", "")
        if not event_id:
            log.warning("ifood_poll_event_missing_id", payload=event_data)
            continue

        event_ids_to_ack.append(event_id)

        # Idempotency: skip if RawEvent with same source+event_id already exists
        already_exists = RawEvent.objects.filter(source="ifood", event_id=event_id).exists()
        if already_exists:
            log.debug("ifood_poll_event_duplicate_skipped", event_id=event_id)
            continue

        event_type = event_data.get("code", "") or event_data.get("type", "")

        raw_event = RawEvent.objects.create(
            source="ifood",
            event_id=event_id,
            event_type=event_type,
            tenant_id=cred.store.company.tenant_id,
            store_id=cred.store_id,
            payload=event_data,
            headers={"ingestion": "polling"},
            status=RawEventStatus.RECEIVED,
        )

        process_ifood_event.delay(str(raw_event.id))

        raw_event.status = RawEventStatus.ENQUEUED
        raw_event.save(update_fields=["status"])

        new_count += 1

        log.info(
            "ifood_poll_event_created",
            event_id=event_id,
            event_type=event_type,
            raw_event_id=str(raw_event.id),
            store_id=str(cred.store_id),
        )

    # Acknowledge ALL fetched events (including duplicates) so they leave the queue
    client.acknowledge_events(event_ids_to_ack)

    return new_count
