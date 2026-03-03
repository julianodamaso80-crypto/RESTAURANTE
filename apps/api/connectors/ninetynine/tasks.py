import structlog
import structlog.contextvars
from celery import shared_task
from django.utils import timezone

log = structlog.get_logger()

ORDER_CREATED_EVENTS = {"PLACED", "ORDER_PLACED", "CREATED", "NEW"}


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=120,
)
def process_ninetynine_event(self, raw_event_id: str):
    """Async 99Food pipeline — identical to iFood.

    1. Load RawEvent (source='99food')
    2. Check idempotency
    3. Fetch details from 99Food API
    4. Map to internal Order
    5. Create Order + IdempotencyKey
    6. Mark RawEvent as PROCESSED
    """
    from connectors.ifood.models import RawEvent, RawEventStatus
    from orders.models import IdempotencyKey, Order, OrderItem

    from .mapper import map_ninetynine_order_to_internal

    structlog.contextvars.bind_contextvars(
        raw_event_id=raw_event_id,
        task_id=self.request.id,
        connector="99food",
    )

    log.info("99food_event_processing_started")

    try:
        raw_event = RawEvent.objects.get(id=raw_event_id, source="99food")
    except RawEvent.DoesNotExist:
        log.error("99food_raw_event_not_found")
        return

    raw_event.status = RawEventStatus.PROCESSING
    raw_event.save(update_fields=["status"])

    event_id = raw_event.event_id
    payload = raw_event.payload
    event_type = raw_event.event_type

    structlog.contextvars.bind_contextvars(event_id=event_id, event_type=event_type)

    # Only process order creation events
    if event_type.upper() not in ORDER_CREATED_EVENTS:
        log.info("99food_event_skipped_non_order", event_type=event_type)
        raw_event.status = RawEventStatus.PROCESSED
        raw_event.processed_at = timezone.now()
        raw_event.save(update_fields=["status", "processed_at"])
        return

    # Idempotency
    merchant_id = payload.get("merchantId", "")
    store = _resolve_store(merchant_id)

    idempotency_key = f"99food:{event_id}"

    if store:
        existing = (
            IdempotencyKey.objects.filter(tenant=store.company.tenant, key=idempotency_key)
            .select_related("order")
            .first()
        )

        if existing and existing.order:
            log.info("99food_event_duplicate_skipped", existing_order_id=str(existing.order.id))
            raw_event.status = RawEventStatus.DUPLICATE
            raw_event.processed_at = timezone.now()
            raw_event.save(update_fields=["status", "processed_at"])
            return

    # Fetch details from API
    order_id_99 = payload.get("orderId") or payload.get("id", "")
    order_detail = _fetch_order_with_retry(order_id_99, store)

    if order_detail is None:
        raw_event.retry_count += 1
        raw_event.save(update_fields=["retry_count"])
        raise Exception(f"Could not fetch 99Food order {order_id_99} — will retry")

    if not store:
        log.error("99food_store_not_found", merchant_id=merchant_id)
        raw_event.status = RawEventStatus.FAILED
        raw_event.error_detail = f"Store not found for merchant_id: {merchant_id}"
        raw_event.save(update_fields=["status", "error_detail"])
        return

    tenant = store.company.tenant
    order_data = map_ninetynine_order_to_internal(order_detail, tenant, store)

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
        "99food_order_created",
        order_id=str(order.id),
        external_id=order.external_id,
        total_cents=order.total_cents,
    )


def _resolve_store(merchant_id: str):
    if not merchant_id:
        return None
    try:
        from .models import NinetyNineStoreCredential

        cred = (
            NinetyNineStoreCredential.objects.filter(merchant_id=merchant_id, is_active=True)
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
        from .client import NinetyNineAPIClient, NinetyNineOrderNotFoundError
        from .models import NinetyNineStoreCredential

        cred = NinetyNineStoreCredential.objects.filter(store=store, is_active=True).first()

        if not cred or not cred.access_token:
            log.warning("99food_no_access_token", store_id=str(store.id))
            return None

        client = NinetyNineAPIClient(access_token=cred.access_token)
        return client.get_order(order_id)

    except NinetyNineOrderNotFoundError:
        log.error("99food_order_not_found_after_retries", order_id=order_id)
        return None
    except Exception as exc:
        log.error("99food_fetch_error", order_id=order_id, error=str(exc))
        return None
