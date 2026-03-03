from decimal import Decimal
from unittest.mock import patch

from orders.enums import OrderStatus
from stock.models import MovementType, StockAlert, StockLevel, StockMovement


class TestRecalculateStockLevel:
    def test_recalculate_creates_level(self, stock_item_factory, stock_movement_factory, store):
        from stock.tasks import recalculate_stock_level

        item = stock_item_factory(store=store, minimum_stock=Decimal("5.000"))
        stock_movement_factory(stock_item=item, type=MovementType.ENTRADA, quantity=Decimal("20.000"))

        recalculate_stock_level(str(item.id))

        level = StockLevel.objects.get(stock_item=item)
        assert level.current_quantity == Decimal("20.000")
        assert level.is_below_minimum is False

    def test_recalculate_with_exits(self, stock_item_factory, stock_movement_factory, store):
        from stock.tasks import recalculate_stock_level

        item = stock_item_factory(store=store, minimum_stock=Decimal("5.000"))
        stock_movement_factory(stock_item=item, type=MovementType.ENTRADA, quantity=Decimal("20.000"))
        stock_movement_factory(stock_item=item, type=MovementType.SAIDA, quantity=Decimal("-12.000"))

        recalculate_stock_level(str(item.id))

        level = StockLevel.objects.get(stock_item=item)
        assert level.current_quantity == Decimal("8.000")
        assert level.is_below_minimum is False

    def test_recalculate_creates_alert_below_minimum(self, stock_item_factory, stock_movement_factory, store):
        from stock.tasks import recalculate_stock_level

        item = stock_item_factory(store=store, minimum_stock=Decimal("10.000"))
        stock_movement_factory(stock_item=item, type=MovementType.ENTRADA, quantity=Decimal("3.000"))

        recalculate_stock_level(str(item.id))

        level = StockLevel.objects.get(stock_item=item)
        assert level.is_below_minimum is True
        assert StockAlert.objects.filter(stock_item=item, is_resolved=False).exists()

    def test_recalculate_resolves_alert_when_above_minimum(self, stock_item_factory, stock_movement_factory, store):
        from stock.tasks import recalculate_stock_level

        item = stock_item_factory(store=store, minimum_stock=Decimal("5.000"))
        stock_movement_factory(stock_item=item, type=MovementType.ENTRADA, quantity=Decimal("2.000"))

        recalculate_stock_level(str(item.id))
        assert StockAlert.objects.filter(stock_item=item, is_resolved=False).exists()

        # Agora adiciona mais e recalcula
        stock_movement_factory(stock_item=item, type=MovementType.ENTRADA, quantity=Decimal("10.000"))
        recalculate_stock_level(str(item.id))

        level = StockLevel.objects.get(stock_item=item)
        assert level.current_quantity == Decimal("12.000")
        assert level.is_below_minimum is False
        assert not StockAlert.objects.filter(stock_item=item, is_resolved=False).exists()
        assert StockAlert.objects.filter(stock_item=item, is_resolved=True).exists()

    def test_recalculate_no_duplicate_alerts(self, stock_item_factory, stock_movement_factory, store):
        from stock.tasks import recalculate_stock_level

        item = stock_item_factory(store=store, minimum_stock=Decimal("10.000"))
        stock_movement_factory(stock_item=item, type=MovementType.ENTRADA, quantity=Decimal("2.000"))

        recalculate_stock_level(str(item.id))
        recalculate_stock_level(str(item.id))

        alerts = StockAlert.objects.filter(stock_item=item, is_resolved=False)
        assert alerts.count() == 1

    def test_recalculate_nonexistent_item(self, db):
        import uuid

        from stock.tasks import recalculate_stock_level

        # Should not raise — just logs error
        recalculate_stock_level(str(uuid.uuid4()))

    def test_recalculate_updates_existing_level(self, stock_item_factory, stock_movement_factory, store):
        from stock.tasks import recalculate_stock_level

        item = stock_item_factory(store=store, minimum_stock=Decimal("5.000"))
        stock_movement_factory(stock_item=item, type=MovementType.ENTRADA, quantity=Decimal("10.000"))
        recalculate_stock_level(str(item.id))

        stock_movement_factory(stock_item=item, type=MovementType.ENTRADA, quantity=Decimal("5.000"))
        recalculate_stock_level(str(item.id))

        level = StockLevel.objects.get(stock_item=item)
        assert level.current_quantity == Decimal("15.000")


class TestDebitStockForOrder:
    def test_debit_creates_movements(
        self,
        store,
        order_factory,
        order_item_factory,
        stock_item_factory,
        bom_factory,
        product_factory,
        product_channel_map_factory,
    ):
        from stock.tasks import debit_stock_for_order

        product = product_factory()
        product_channel_map_factory(product=product, external_id="ext-pizza")
        item = stock_item_factory(name="Mussarela", store=store)
        bom_factory(product=product, stock_item=item, quantity_per_unit=Decimal("0.300"))

        # Create with PENDING to avoid signal triggering .delay() (no Redis in tests)
        order = order_factory(status=OrderStatus.PENDING)
        order_item_factory(order=order, external_item_id="ext-pizza", quantity=2)

        with patch("stock.tasks.recalculate_stock_level.delay"):
            debit_stock_for_order(str(order.id))

        mov = StockMovement.objects.filter(reference_type="order", reference_id=str(order.id))
        assert mov.count() == 1
        assert mov.first().quantity == Decimal("-0.600")

    def test_debit_idempotent(
        self,
        store,
        order_factory,
        order_item_factory,
        stock_item_factory,
        bom_factory,
        product_factory,
        product_channel_map_factory,
    ):
        from stock.tasks import debit_stock_for_order

        product = product_factory()
        product_channel_map_factory(product=product, external_id="ext-burger")
        item = stock_item_factory(name="Carne", store=store)
        bom_factory(product=product, stock_item=item, quantity_per_unit=Decimal("0.180"))

        order = order_factory(status=OrderStatus.PENDING)
        order_item_factory(order=order, external_item_id="ext-burger", quantity=1)

        with patch("stock.tasks.recalculate_stock_level.delay"):
            debit_stock_for_order(str(order.id))
            debit_stock_for_order(str(order.id))

        mov = StockMovement.objects.filter(reference_type="order", reference_id=str(order.id))
        assert mov.count() == 1

    def test_debit_skips_items_without_external_id(
        self,
        store,
        order_factory,
        order_item_factory,
    ):
        from stock.tasks import debit_stock_for_order

        order = order_factory(status=OrderStatus.PENDING)
        order_item_factory(order=order, external_item_id=None, quantity=1)

        debit_stock_for_order(str(order.id))

        assert StockMovement.objects.filter(reference_type="order").count() == 0

    def test_debit_nonexistent_order(self, db):
        import uuid

        from stock.tasks import debit_stock_for_order

        # Should not raise — just logs error
        debit_stock_for_order(str(uuid.uuid4()))

    def test_debit_multiple_bom_items(
        self,
        store,
        order_factory,
        order_item_factory,
        stock_item_factory,
        bom_factory,
        product_factory,
        product_channel_map_factory,
    ):
        from stock.tasks import debit_stock_for_order

        product = product_factory()
        product_channel_map_factory(product=product, external_id="ext-combo")
        item1 = stock_item_factory(name="Arroz", store=store)
        item2 = stock_item_factory(name="Feijão", store=store)
        bom_factory(product=product, stock_item=item1, quantity_per_unit=Decimal("0.300"))
        bom_factory(product=product, stock_item=item2, quantity_per_unit=Decimal("0.200"))

        order = order_factory(status=OrderStatus.PENDING)
        order_item_factory(order=order, external_item_id="ext-combo", quantity=2)

        with patch("stock.tasks.recalculate_stock_level.delay"):
            debit_stock_for_order(str(order.id))

        movs = StockMovement.objects.filter(reference_type="order", reference_id=str(order.id))
        assert movs.count() == 2
        total_debited = sum(m.quantity for m in movs)
        assert total_debited == Decimal("-1.000")  # (0.3+0.2)*2
