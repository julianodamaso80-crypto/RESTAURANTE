import structlog
from django.db.models.signals import post_save
from django.dispatch import receiver

log = structlog.get_logger()


@receiver(post_save, sender="orders.Order")
def handle_order_delivered(sender, instance, **kwargs):
    """Quando Order -> DELIVERED:

    1. Registra CustomerEvent
    2. Dispara recálculo RFV assincronamente
    """
    from orders.enums import OrderStatus

    from .models import CustomerEvent, CustomerEventType
    from .tasks import recalculate_customer_rfv

    if instance.status != OrderStatus.DELIVERED:
        return

    customer = _find_or_skip_customer(instance)
    if not customer:
        log.info("cdp_no_customer_for_order", order_id=str(instance.id))
        return

    # Registrar evento (idempotente via get_or_create)
    CustomerEvent.objects.get_or_create(
        customer=customer,
        event_type=CustomerEventType.ORDER_DELIVERED,
        payload={"order_id": str(instance.id)},
        defaults={"store": instance.store, "occurred_at": instance.delivered_at},
    )

    # Recalcular RFV assincronamente
    recalculate_customer_rfv.delay(str(customer.id))

    log.info("cdp_order_delivered_event_recorded", customer_id=str(customer.id), order_id=str(instance.id))


def _find_or_skip_customer(order):
    """Tenta encontrar Customer pelo conteúdo do order.

    Retorna None se não encontrado (não cria automaticamente).
    """
    from .models import CustomerIdentity

    # Busca via external_id do pedido -> CustomerIdentity
    if order.external_id:
        identity = (
            CustomerIdentity.objects.filter(
                customer__tenant=order.tenant,
                value=order.external_id,
            )
            .select_related("customer")
            .first()
        )
        if identity:
            return identity.customer

    return None
