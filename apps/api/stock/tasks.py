import structlog
import structlog.contextvars
from celery import shared_task
from django.db.models import Sum
from django.utils import timezone

log = structlog.get_logger()


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def recalculate_stock_level(self, stock_item_id: str):
    """Recalcula StockLevel somando todos os StockMovements do item.

    Fonte da verdade: StockMovement.
    Cria alerta se saldo < mínimo.
    """
    from decimal import Decimal

    from .models import StockAlert, StockItem, StockLevel, StockMovement

    try:
        item = StockItem.objects.get(id=stock_item_id)
    except StockItem.DoesNotExist:
        log.error("stock_item_not_found", stock_item_id=stock_item_id)
        return

    # Somar todos os movimentos (positivos e negativos)
    result = StockMovement.objects.filter(stock_item=item).aggregate(total=Sum("quantity"))
    current_qty = result["total"] or Decimal("0")

    last_movement = StockMovement.objects.filter(stock_item=item).order_by("-occurred_at").first()

    is_below = current_qty < item.minimum_stock

    StockLevel.objects.update_or_create(
        stock_item=item,
        defaults={
            "current_quantity": current_qty,
            "is_below_minimum": is_below,
            "last_movement_at": last_movement.occurred_at if last_movement else None,
            "calculated_at": timezone.now(),
        },
    )

    # Criar alerta se abaixo do mínimo e não há alerta aberto
    if is_below:
        existing_alert = StockAlert.objects.filter(stock_item=item, is_resolved=False).exists()
        if not existing_alert:
            StockAlert.objects.create(
                stock_item=item,
                store=item.store,
                current_qty=current_qty,
                minimum_qty=item.minimum_stock,
            )
            log.warning(
                "stock_below_minimum",
                item=item.name,
                current=float(current_qty),
                minimum=float(item.minimum_stock),
            )
    else:
        # Resolver alertas abertos se estoque voltou ao normal
        StockAlert.objects.filter(stock_item=item, is_resolved=False).update(
            is_resolved=True,
            resolved_at=timezone.now(),
        )

    log.info(
        "stock_level_recalculated",
        item=item.name,
        current_qty=float(current_qty),
        is_below=is_below,
    )


@shared_task(bind=True, max_retries=3, default_retry_delay=15)
def debit_stock_for_order(self, order_id: str):
    """Debita estoque para todos os itens de um Order entregue.

    Usa BOM (ficha técnica) para calcular consumo.
    Idempotente: verifica se já existe movimento para este order.
    """
    from decimal import Decimal

    from orders.models import Order

    from .models import BillOfMaterials, MovementType, StockMovement

    structlog.contextvars.bind_contextvars(order_id=order_id)

    try:
        order = Order.objects.prefetch_related("items").get(id=order_id)
    except Order.DoesNotExist:
        log.error("order_not_found_for_stock_debit")
        return

    # Idempotência: se já debitamos este order, não fazer de novo
    already_debited = StockMovement.objects.filter(
        reference_type="order",
        reference_id=order_id,
        type=MovementType.SAIDA,
    ).exists()

    if already_debited:
        log.info("stock_debit_already_done", order_id=order_id)
        return

    debited_items = []

    for order_item in order.items.all():
        if not order_item.external_item_id:
            continue

        # Buscar BOM pelo external_id do canal (snapshot do produto)
        bom_items = BillOfMaterials.objects.filter(
            product__channel_maps__external_id=order_item.external_item_id,
            is_active=True,
        ).select_related("stock_item")

        for bom in bom_items:
            qty_to_debit = bom.quantity_per_unit * Decimal(str(order_item.quantity))

            StockMovement.objects.create(
                stock_item=bom.stock_item,
                store=order.store,
                type=MovementType.SAIDA,
                quantity=-qty_to_debit,  # negativo = saída
                notes=f"Consumo automático — Order #{order.display_number}",
                reference_type="order",
                reference_id=order_id,
            )
            debited_items.append(bom.stock_item.id)

            # Recalcular saldo assincronamente
            recalculate_stock_level.delay(str(bom.stock_item.id))

    log.info(
        "stock_debited_for_order",
        order_id=order_id,
        items_debited=len(debited_items),
    )
