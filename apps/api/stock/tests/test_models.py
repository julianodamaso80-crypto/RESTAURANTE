from decimal import Decimal

import pytest

from stock.models import MovementType, StockAlert, StockItem, StockMovement, StockUnit


class TestStockItem:
    def test_create(self, stock_item_factory):
        item = stock_item_factory(name="Farinha de trigo", unit=StockUnit.KG, minimum_stock=Decimal("10.000"))
        assert item.name == "Farinha de trigo"
        assert item.unit == StockUnit.KG
        assert item.minimum_stock == Decimal("10.000")
        assert item.is_active is True
        assert item.pk is not None

    def test_str(self, stock_item_factory):
        item = stock_item_factory(name="Tomate")
        assert "Tomate" in str(item)

    def test_unique_name_per_store(self, stock_item_factory, store):
        stock_item_factory(name="Cebola", store=store)
        with pytest.raises(Exception):
            stock_item_factory(name="Cebola", store=store)

    def test_ordering_by_name(self, stock_item_factory, store):
        stock_item_factory(name="Banana", store=store)
        stock_item_factory(name="Alface", store=store)
        items = list(StockItem.objects.filter(store=store))
        assert items[0].name == "Alface"
        assert items[1].name == "Banana"

    def test_default_values(self, stock_item_factory):
        item = stock_item_factory()
        assert item.is_active is True
        assert item.notes == ""


class TestStockMovement:
    def test_create_entrada(self, stock_movement_factory, stock_item_factory, store):
        item = stock_item_factory(store=store)
        mov = stock_movement_factory(
            stock_item=item, type=MovementType.ENTRADA, quantity=Decimal("10.000")
        )
        assert mov.type == MovementType.ENTRADA
        assert mov.quantity == Decimal("10.000")
        assert mov.pk is not None

    def test_create_saida(self, stock_movement_factory, stock_item_factory, store):
        item = stock_item_factory(store=store)
        mov = stock_movement_factory(
            stock_item=item, type=MovementType.SAIDA, quantity=Decimal("-5.000")
        )
        assert mov.type == MovementType.SAIDA
        assert mov.quantity == Decimal("-5.000")

    def test_str(self, stock_movement_factory, stock_item_factory, store):
        item = stock_item_factory(name="Farinha", store=store)
        mov = stock_movement_factory(stock_item=item, quantity=Decimal("10.000"))
        assert "Farinha" in str(mov)

    def test_ordering_by_occurred_at_desc(self, stock_movement_factory, stock_item_factory, store):
        from datetime import timedelta

        from django.utils import timezone

        item = stock_item_factory(store=store)
        t1 = timezone.now()
        t2 = t1 + timedelta(seconds=1)
        stock_movement_factory(stock_item=item, occurred_at=t1)
        stock_movement_factory(stock_item=item, occurred_at=t2)
        movs = list(StockMovement.objects.filter(stock_item=item))
        assert movs[0].occurred_at > movs[1].occurred_at

    def test_reference_fields(self, stock_movement_factory, stock_item_factory, store):
        item = stock_item_factory(store=store)
        mov = stock_movement_factory(
            stock_item=item, reference_type="order", reference_id="abc-123"
        )
        assert mov.reference_type == "order"
        assert mov.reference_id == "abc-123"


class TestStockLevel:
    def test_create(self, stock_level_factory, stock_item_factory, store):
        item = stock_item_factory(store=store)
        level = stock_level_factory(
            stock_item=item, current_quantity=Decimal("15.000"), is_below_minimum=False
        )
        assert level.current_quantity == Decimal("15.000")
        assert level.is_below_minimum is False

    def test_str(self, stock_level_factory, stock_item_factory, store):
        item = stock_item_factory(name="Arroz", store=store)
        level = stock_level_factory(stock_item=item, current_quantity=Decimal("20.000"))
        assert "Arroz" in str(level)
        assert "20" in str(level)

    def test_one_to_one(self, stock_level_factory, stock_item_factory, store):
        item = stock_item_factory(store=store)
        stock_level_factory(stock_item=item)
        with pytest.raises(Exception):
            stock_level_factory(stock_item=item)


class TestStockAlert:
    def test_create(self, stock_alert_factory, stock_item_factory, store):
        item = stock_item_factory(store=store)
        alert = stock_alert_factory(
            stock_item=item, current_qty=Decimal("2.000"), minimum_qty=Decimal("5.000")
        )
        assert alert.is_resolved is False
        assert alert.current_qty == Decimal("2.000")
        assert alert.minimum_qty == Decimal("5.000")

    def test_str(self, stock_alert_factory, stock_item_factory, store):
        item = stock_item_factory(name="Leite", store=store)
        alert = stock_alert_factory(stock_item=item)
        assert "Leite" in str(alert)

    def test_ordering_by_created_at_desc(self, stock_alert_factory, stock_item_factory, store):
        from datetime import timedelta

        from django.utils import timezone

        item1 = stock_item_factory(name="Item A", store=store)
        item2 = stock_item_factory(name="Item B", store=store)
        t1 = timezone.now()
        t2 = t1 + timedelta(seconds=1)
        stock_alert_factory(stock_item=item1, created_at=t1)
        stock_alert_factory(stock_item=item2, created_at=t2)
        alerts = list(StockAlert.objects.filter(store=store))
        assert alerts[0].created_at > alerts[1].created_at


class TestBillOfMaterials:
    def test_create(self, bom_factory, stock_item_factory, product_factory, store):
        item = stock_item_factory(store=store)
        product = product_factory()
        bom = bom_factory(product=product, stock_item=item, quantity_per_unit=Decimal("0.200"))
        assert bom.quantity_per_unit == Decimal("0.200")
        assert bom.is_active is True

    def test_str(self, bom_factory, stock_item_factory, product_factory, store):
        item = stock_item_factory(name="Queijo", store=store)
        product = product_factory()
        bom = bom_factory(product=product, stock_item=item)
        assert "Queijo" in str(bom)

    def test_unique_product_stock_item(self, bom_factory, stock_item_factory, product_factory, store):
        item = stock_item_factory(store=store)
        product = product_factory()
        bom_factory(product=product, stock_item=item)
        with pytest.raises(Exception):
            bom_factory(product=product, stock_item=item)

    def test_movement_types(self):
        assert MovementType.ENTRADA == "ENTRADA"
        assert MovementType.SAIDA == "SAIDA"
        assert MovementType.AJUSTE == "AJUSTE"
        assert MovementType.PERDA == "PERDA"
        assert MovementType.INVENTARIO == "INVENTARIO"

    def test_stock_units(self):
        assert StockUnit.KG == "kg"
        assert StockUnit.G == "g"
        assert StockUnit.L == "L"
        assert StockUnit.ML == "mL"
        assert StockUnit.UN == "un"
