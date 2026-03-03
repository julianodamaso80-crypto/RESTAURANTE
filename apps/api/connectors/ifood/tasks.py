import structlog
import structlog.contextvars
from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .client import IFoodOrderNotFoundError

log = structlog.get_logger()


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=120,
)
def process_ifood_event(self, raw_event_id: str):
    """Process iFood event asynchronously.

    Pipeline:
    1. Load RawEvent
    2. Check idempotency (already processed?)
    3. Fetch details from iFood API
    4. Map to internal Order
    5. Create Order + IdempotencyKey
    6. Mark RawEvent as PROCESSED
    """
    from orders.models import IdempotencyKey, Order, OrderItem

    from .mapper import map_ifood_order_to_internal
    from .models import RawEvent, RawEventStatus

    structlog.contextvars.bind_contextvars(
        raw_event_id=raw_event_id,
        task_id=self.request.id,
    )

    log.info("ifood_event_processing_started")

    # 1. Load RawEvent
    try:
        raw_event = RawEvent.objects.get(id=raw_event_id)
    except RawEvent.DoesNotExist:
        log.error("ifood_raw_event_not_found")
        return

    raw_event.status = RawEventStatus.PROCESSING
    raw_event.save(update_fields=["status"])

    event_id = raw_event.event_id
    payload = raw_event.payload
    event_type = raw_event.event_type

    structlog.contextvars.bind_contextvars(event_id=event_id, event_type=event_type)

    # 2. Idempotency — only process order creation events
    ORDER_CREATED_EVENTS = {"PLACED", "ORDER_PLACED", "CREATED"}
    if event_type.upper() not in ORDER_CREATED_EVENTS:
        log.info("ifood_event_skipped_non_order", event_type=event_type)
        raw_event.status = RawEventStatus.PROCESSED
        raw_event.processed_at = timezone.now()
        raw_event.save(update_fields=["status", "processed_at"])
        return

    # 3. Check idempotency key
    idempotency_key = f"ifood:{event_id}"

    # Resolve tenant/store by merchant_id
    merchant_id = payload.get("merchantId", "")
    store = _resolve_store(merchant_id)

    if store:
        existing_key = (
            IdempotencyKey.objects.filter(tenant=store.company.tenant, key=idempotency_key)
            .select_related("order")
            .first()
        )

        if existing_key and existing_key.order:
            log.info("ifood_event_duplicate_skipped", existing_order_id=str(existing_key.order.id))
            raw_event.status = RawEventStatus.DUPLICATE
            raw_event.processed_at = timezone.now()
            raw_event.save(update_fields=["status", "processed_at"])
            return

    # 4. Fetch details from iFood API (with retry for transient 404)
    order_id_ifood = payload.get("orderId") or payload.get("id", "")
    ifood_order_detail = _fetch_ifood_order_with_retry(order_id_ifood, store)

    if ifood_order_detail is None:
        raw_event.retry_count += 1
        raw_event.save(update_fields=["retry_count"])
        raise Exception(f"Could not fetch iFood order {order_id_ifood} — will retry")

    # 5. Map to internal Order
    if not store:
        log.error("ifood_store_not_found", merchant_id=merchant_id)
        raw_event.status = RawEventStatus.FAILED
        raw_event.error_detail = f"Store not found for merchant_id: {merchant_id}"
        raw_event.save(update_fields=["status", "error_detail"])
        return

    tenant = store.company.tenant
    order_data = map_ifood_order_to_internal(ifood_order_detail, tenant, store)

    # 6. Create Order and IdempotencyKey in atomic transaction
    with transaction.atomic():
        items_data = order_data.pop("items", [])
        order = Order.objects.create(**order_data)

        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)

        IdempotencyKey.objects.get_or_create(tenant=tenant, key=idempotency_key, defaults={"order": order})

        raw_event.status = RawEventStatus.PROCESSED
        raw_event.processed_at = timezone.now()
        raw_event.save(update_fields=["status", "processed_at"])

    log.info(
        "ifood_order_created",
        order_id=str(order.id),
        external_id=order.external_id,
        total_cents=order.total_cents,
    )


def _resolve_store(merchant_id: str):
    """Resolve Store by iFood merchant_id. Returns None if not found."""
    if not merchant_id:
        return None
    try:
        from .models import IFoodStoreCredential

        cred = (
            IFoodStoreCredential.objects.filter(merchant_id=merchant_id, is_active=True)
            .select_related("store__company__tenant")
            .first()
        )
        return cred.store if cred else None
    except Exception:
        return None


def _fetch_ifood_order_with_retry(order_id: str, store) -> dict | None:
    """Fetch order details from iFood API. Returns None if unable after retries."""
    if not order_id or not store:
        return None

    try:
        from .client import IFoodAPIClient
        from .models import IFoodStoreCredential

        cred = IFoodStoreCredential.objects.filter(store=store, is_active=True).first()

        if not cred or not cred.access_token:
            log.warning("ifood_no_access_token", store_id=str(store.id))
            return None

        client = IFoodAPIClient(access_token=cred.access_token)
        return client.get_order(order_id)

    except IFoodOrderNotFoundError:
        log.error("ifood_order_not_found_after_retries", order_id=order_id)
        return None
    except Exception as exc:
        log.error("ifood_fetch_error", order_id=order_id, error=str(exc))
        return None
