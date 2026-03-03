from decimal import Decimal

from stock.models import BillOfMaterials


class TestBillOfMaterials:
    def test_bom_lookup_by_channel_map(
        self, bom_factory, stock_item_factory, product_factory, product_channel_map_factory, store
    ):
        """BOM deve ser encontrável via ProductChannelMap.external_id."""
        product = product_factory()
        product_channel_map_factory(product=product, external_id="ext-ifood-001")
        item = stock_item_factory(store=store)
        bom_factory(product=product, stock_item=item, quantity_per_unit=Decimal("0.300"))

        bom_qs = BillOfMaterials.objects.filter(
            product__channel_maps__external_id="ext-ifood-001",
            is_active=True,
        )
        assert bom_qs.count() == 1
        assert bom_qs.first().stock_item == item

    def test_bom_inactive_excluded(
        self, bom_factory, stock_item_factory, product_factory, product_channel_map_factory, store
    ):
        product = product_factory()
        product_channel_map_factory(product=product, external_id="ext-002")
        item = stock_item_factory(store=store)
        bom_factory(product=product, stock_item=item, is_active=False)

        bom_qs = BillOfMaterials.objects.filter(
            product__channel_maps__external_id="ext-002",
            is_active=True,
        )
        assert bom_qs.count() == 0

    def test_bom_multiple_ingredients(
        self, bom_factory, stock_item_factory, product_factory, store
    ):
        """Um produto pode ter vários insumos na ficha técnica."""
        product = product_factory()
        item1 = stock_item_factory(name="Farinha", store=store)
        item2 = stock_item_factory(name="Queijo", store=store)
        bom_factory(product=product, stock_item=item1, quantity_per_unit=Decimal("0.200"))
        bom_factory(product=product, stock_item=item2, quantity_per_unit=Decimal("0.100"))

        boms = BillOfMaterials.objects.filter(product=product, is_active=True)
        assert boms.count() == 2

    def test_bom_quantity_calculation(
        self, bom_factory, stock_item_factory, product_factory, store
    ):
        """Verifica cálculo: qty vendida * quantity_per_unit."""
        product = product_factory()
        item = stock_item_factory(store=store)
        bom_factory(product=product, stock_item=item, quantity_per_unit=Decimal("0.250"))

        bom = BillOfMaterials.objects.get(product=product, stock_item=item)
        qty_sold = Decimal("3")
        consumed = bom.quantity_per_unit * qty_sold
        assert consumed == Decimal("0.750")
