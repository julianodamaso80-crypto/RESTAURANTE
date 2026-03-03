from decimal import Decimal

import factory
from factory.django import DjangoModelFactory

from orders.tests.factories import StoreFactory
from stock.models import (
    BillOfMaterials,
    MovementType,
    StockAlert,
    StockItem,
    StockLevel,
    StockMovement,
    StockUnit,
)


class StockItemFactory(DjangoModelFactory):
    class Meta:
        model = StockItem

    store = factory.SubFactory(StoreFactory)
    name = factory.Sequence(lambda n: f"Insumo {n}")
    unit = StockUnit.KG
    minimum_stock = Decimal("5.000")
    is_active = True


class StockMovementFactory(DjangoModelFactory):
    class Meta:
        model = StockMovement

    stock_item = factory.SubFactory(StockItemFactory)
    store = factory.LazyAttribute(lambda o: o.stock_item.store)
    type = MovementType.ENTRADA
    quantity = Decimal("10.000")
    notes = "Entrada de teste"


class StockLevelFactory(DjangoModelFactory):
    class Meta:
        model = StockLevel

    stock_item = factory.SubFactory(StockItemFactory)
    current_quantity = Decimal("10.000")
    is_below_minimum = False


class StockAlertFactory(DjangoModelFactory):
    class Meta:
        model = StockAlert

    stock_item = factory.SubFactory(StockItemFactory)
    store = factory.LazyAttribute(lambda o: o.stock_item.store)
    current_qty = Decimal("2.000")
    minimum_qty = Decimal("5.000")
    is_resolved = False


class BillOfMaterialsFactory(DjangoModelFactory):
    class Meta:
        model = BillOfMaterials

    product = factory.SubFactory("catalog.tests.factories.ProductFactory")
    stock_item = factory.SubFactory(StockItemFactory)
    quantity_per_unit = Decimal("0.200")
    is_active = True
