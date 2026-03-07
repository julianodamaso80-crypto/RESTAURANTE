import structlog
import structlog.contextvars
from celery import shared_task
from django.utils import timezone

log = structlog.get_logger()

ORDER_CREATED_EVENTS = {"NEW_ORDER", "PLACED", "ORDER_PLACED", "CREATED", "NEW"}


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=120,
)
def process_rappi_event(self, raw_event_id: str):
    """Async Rappi pipeline — same pattern as iFood/99Food.

    1. Load RawEvent (source='rappi')
    2. Check idempotency
    3. Fetch details from Rappi API
    4. Map to internal Order
    5. Create Order + IdempotencyKey
    6. Mark RawEvent as PROCESSED
    """
    from connectors.ifood.models import RawEvent, RawEventStatus
    from orders.models import IdempotencyKey, Order, OrderItem

    from .mapper import map_rappi_order_to_internal

    structlog.contextvars.bind_contextvars(
        raw_event_id=raw_event_id,
        task_id=self.request.id,
        connector="rappi",
    )

    log.info("rappi_event_processing_started")

    try:
        raw_event = RawEvent.objects.get(id=raw_event_id, source="rappi")
    except RawEvent.DoesNotExist:
        log.error("rappi_raw_event_not_found")
        return

    raw_event.status = RawEventStatus.PROCESSING
    raw_event.save(update_fields=["status"])

    event_id = raw_event.event_id
    payload = raw_event.payload
    event_type = raw_event.event_type

    structlog.contextvars.bind_contextvars(event_id=event_id, event_type=event_type)

    if event_type.upper() not in ORDER_CREATED_EVENTS:
        log.info("rappi_event_skipped_non_order", event_type=event_type)
        raw_event.status = RawEventStatus.PROCESSED
        raw_event.processed_at = timezone.now()
        raw_event.save(update_fields=["status", "processed_at"])
        return

    rappi_store_id = payload.get("store_id", "") or payload.get("storeId", "")
    store = _resolve_store(rappi_store_id)

    idempotency_key = f"rappi:{event_id}"

    if store:
        existing = (
            IdempotencyKey.objects.filter(tenant=store.company.tenant, key=idempotency_key)
            .select_related("order")
            .first()
        )

        if existing and existing.order:
            log.info("rappi_event_duplicate_skipped", existing_order_id=str(existing.order.id))
            raw_event.status = RawEventStatus.DUPLICATE
            raw_event.processed_at = timezone.now()
            raw_event.save(update_fields=["status", "processed_at"])
            return

    order_id_rappi = payload.get("orderId") or payload.get("id", "")
    order_detail = _fetch_order_with_retry(order_id_rappi, store)

    if order_detail is None:
        raw_event.retry_count += 1
        raw_event.save(update_fields=["retry_count"])
        raise Exception(f"Could not fetch Rappi order {order_id_rappi} — will retry")

    if not store:
        log.error("rappi_store_not_found", rappi_store_id=rappi_store_id)
        raw_event.status = RawEventStatus.FAILED
        raw_event.error_detail = f"Store not found for rappi_store_id: {rappi_store_id}"
        raw_event.save(update_fields=["status", "error_detail"])
        return

    tenant = store.company.tenant
    order_data = map_rappi_order_to_internal(order_detail, tenant, store)

    from django.db import transaction

    with transaction.atomic():
        items_data = order_data.pop("items", [])
        order = Order.objects.create(**order_data)

        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)

        IdempotencyKey.objects.get_or_create(
            tenant=tenant,
            key=idempotency_key,
            defaults={"order": order},
        )

        raw_event.status = RawEventStatus.PROCESSED
        raw_event.processed_at = timezone.now()
        raw_event.save(update_fields=["status", "processed_at"])

    log.info(
        "rappi_order_created",
        order_id=str(order.id),
        external_id=order.external_id,
        total_cents=order.total_cents,
    )


def _resolve_store(rappi_store_id: str):
    if not rappi_store_id:
        return None
    try:
        from .models import RappiStoreCredential

        cred = (
            RappiStoreCredential.objects.filter(rappi_store_id=rappi_store_id, is_active=True)
            .select_related("store__company__tenant")
            .first()
        )
        return cred.store if cred else None
    except Exception:
        return None


def _fetch_order_with_retry(order_id: str, store) -> dict | None:
    if not order_id or not store:
        return None
    try:
        from .client import RappiAPIClient, RappiOrderNotFoundError
        from .models import RappiStoreCredential

        cred = RappiStoreCredential.objects.filter(store=store, is_active=True).first()

        if not cred or not cred.rappi_token:
            log.warning("rappi_no_token", store_id=str(store.id))
            return None

        client = RappiAPIClient(rappi_token=cred.rappi_token, base_url=cred.base_url)
        return client.get_order(order_id)

    except RappiOrderNotFoundError:
        log.error("rappi_order_not_found_after_retries", order_id=order_id)
        return None
    except Exception as exc:
        log.error("rappi_fetch_error", order_id=order_id, error=str(exc))
        return None
