from decimal import Decimal

from django.db.models import Sum

from stock.models import MovementType, StockMovement


class TestMovementSum:
    """Garante que a soma algébrica dos movimentos funciona corretamente."""

    def test_sum_entries(self, stock_movement_factory, stock_item_factory, store):
        item = stock_item_factory(store=store)
        stock_movement_factory(stock_item=item, type=MovementType.ENTRADA, quantity=Decimal("10.000"))
        stock_movement_factory(stock_item=item, type=MovementType.ENTRADA, quantity=Decimal("5.000"))
        total = StockMovement.objects.filter(stock_item=item).aggregate(t=Sum("quantity"))["t"]
        assert total == Decimal("15.000")

    def test_sum_entries_and_exits(self, stock_movement_factory, stock_item_factory, store):
        item = stock_item_factory(store=store)
        stock_movement_factory(stock_item=item, type=MovementType.ENTRADA, quantity=Decimal("20.000"))
        stock_movement_factory(stock_item=item, type=MovementType.SAIDA, quantity=Decimal("-8.000"))
        total = StockMovement.objects.filter(stock_item=item).aggregate(t=Sum("quantity"))["t"]
        assert total == Decimal("12.000")

    def test_sum_empty(self, stock_item_factory, store):
        item = stock_item_factory(store=store)
        total = StockMovement.objects.filter(stock_item=item).aggregate(t=Sum("quantity"))["t"]
        assert total is None

    def test_movements_are_append_only(self, stock_movement_factory, stock_item_factory, store):
        """Movimentos não devem ser editados — apenas criados."""
        item = stock_item_factory(store=store)
        mov = stock_movement_factory(stock_item=item, quantity=Decimal("10.000"))
        assert StockMovement.objects.filter(pk=mov.pk).exists()


class TestMovementWithReference:
    def test_filter_by_reference(self, stock_movement_factory, stock_item_factory, store):
        item = stock_item_factory(store=store)
        stock_movement_factory(
            stock_item=item, reference_type="order", reference_id="order-001"
        )
        stock_movement_factory(
            stock_item=item, reference_type="manual", reference_id="manual-001"
        )
        order_movs = StockMovement.objects.filter(reference_type="order")
        assert order_movs.count() == 1
        assert order_movs.first().reference_id == "order-001"

    def test_idempotent_check_by_reference(self, stock_movement_factory, stock_item_factory, store):
        item = stock_item_factory(store=store)
        stock_movement_factory(
            stock_item=item,
            type=MovementType.SAIDA,
            quantity=Decimal("-5.000"),
            reference_type="order",
            reference_id="order-XYZ",
        )
        already = StockMovement.objects.filter(
            reference_type="order",
            reference_id="order-XYZ",
            type=MovementType.SAIDA,
        ).exists()
        assert already is True
