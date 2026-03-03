import structlog
from celery import shared_task
from django.db.models import Count, Q, Sum
from django.utils import timezone

log = structlog.get_logger()


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def recalculate_customer_rfv(self, customer_id: str):
    """Recalcula RFV (Recência, Frequência, Valor) de um Customer.

    Chamado assincronamente quando Order -> DELIVERED.
    Nunca chamado de forma síncrona em requests.
    """
    from .models import Customer

    try:
        customer = Customer.objects.get(id=customer_id)
    except Customer.DoesNotExist:
        log.error("rfv_customer_not_found", customer_id=customer_id)
        return

    structlog.contextvars.bind_contextvars(customer_id=customer_id)

    delivered_orders = _get_customer_orders(customer)

    if not delivered_orders.exists():
        log.info("rfv_no_orders_found", customer_id=customer_id)
        return

    stats = delivered_orders.aggregate(
        total_orders=Count("id"),
        total_spent=Sum("total_cents"),
    )

    last_order = delivered_orders.order_by("-delivered_at").first()
    last_order_at = last_order.delivered_at if last_order else None

    recency_days = None
    if last_order_at:
        recency_days = (timezone.now() - last_order_at).days

    customer.rfv_frequency = stats["total_orders"] or 0
    customer.rfv_monetary_cents = stats["total_spent"] or 0
    customer.rfv_recency_days = recency_days
    customer.rfv_last_order_at = last_order_at
    customer.rfv_calculated_at = timezone.now()
    customer.save(
        update_fields=[
            "rfv_frequency",
            "rfv_monetary_cents",
            "rfv_recency_days",
            "rfv_last_order_at",
            "rfv_calculated_at",
        ]
    )

    log.info(
        "rfv_recalculated",
        customer_id=customer_id,
        frequency=customer.rfv_frequency,
        monetary_cents=customer.rfv_monetary_cents,
        recency_days=recency_days,
    )


def _get_customer_orders(customer):
    """Retorna queryset de Orders entregues vinculados ao Customer.

    Estratégia: match por identidades conhecidas no external_id dos orders.
    Em PR futuro, Order terá FK opcional para Customer.
    """
    from orders.enums import OrderStatus
    from orders.models import Order

    identity_values = list(customer.identities.values_list("value", flat=True))

    if not identity_values and not customer.phone and not customer.email:
        return Order.objects.none()

    filters = Q(tenant=customer.tenant, status=OrderStatus.DELIVERED)

    # Match por phone no campo notes (temporário — em PR futuro Order terá customer_phone)
    if customer.phone:
        filters &= Q(notes__icontains=customer.phone)

    return Order.objects.filter(filters)
