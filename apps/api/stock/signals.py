import structlog
from django.db.models.signals import post_save
from django.dispatch import receiver

log = structlog.get_logger()


@receiver(post_save, sender="orders.Order")
def handle_order_delivered_stock(sender, instance, **kwargs):
    """Quando Order → DELIVERED, debita estoque via BOM assincronamente.

    Não interfere com o signal do CDP (cdp/signals.py) — são independentes.
    """
    from orders.enums import OrderStatus

    from .tasks import debit_stock_for_order

    if instance.status != OrderStatus.DELIVERED:
        return

    debit_stock_for_order.delay(str(instance.id))
    log.info("stock_debit_enqueued", order_id=str(instance.id))
