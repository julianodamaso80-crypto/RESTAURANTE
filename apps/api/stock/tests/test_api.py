from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse


class TestStockItemAPI:
    def test_list_empty(self, auth_client):
        url = reverse("stock-item-list")
        resp = auth_client.get(url)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_item(self, auth_client):
        url = reverse("stock-item-list")
        payload = {
            "name": "Farinha de trigo",
            "unit": "kg",
            "minimum_stock": "10.000",
        }
        resp = auth_client.post(url, payload, format="json")
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Farinha de trigo"
        assert data["unit"] == "kg"

    def test_list_items(self, auth_client, stock_item_factory, store):
        stock_item_factory(name="Arroz", store=store)
        stock_item_factory(name="Feijão", store=store)
        url = reverse("stock-item-list")
        resp = auth_client.get(url)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_patch_item(self, auth_client, stock_item_factory, store):
        item = stock_item_factory(name="Arroz", store=store)
        url = reverse("stock-item-detail", args=[str(item.id)])
        resp = auth_client.patch(url, {"minimum_stock": "20.000"}, format="json")
        assert resp.status_code == 200
        assert resp.json()["minimum_stock"] == "20.000"

    def test_delete_item(self, auth_client, stock_item_factory, store):
        item = stock_item_factory(name="Descartável", store=store)
        url = reverse("stock-item-detail", args=[str(item.id)])
        resp = auth_client.delete(url)
        assert resp.status_code == 204

    def test_item_includes_level(self, auth_client, stock_item_factory, stock_level_factory, store):
        item = stock_item_factory(store=store)
        stock_level_factory(stock_item=item, current_quantity=Decimal("15.000"))
        url = reverse("stock-item-detail", args=[str(item.id)])
        resp = auth_client.get(url)
        assert resp.status_code == 200
        assert resp.json()["level"]["current_quantity"] == "15.000"

    def test_item_movements_action(self, auth_client, stock_item_factory, stock_movement_factory, store):
        item = stock_item_factory(store=store)
        stock_movement_factory(stock_item=item, quantity=Decimal("10.000"))
        url = reverse("stock-item-movements", args=[str(item.id)])
        resp = auth_client.get(url)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_item_recalculate_action(self, auth_client, stock_item_factory, store):
        item = stock_item_factory(store=store)
        url = reverse("stock-item-recalculate", args=[str(item.id)])
        with patch("stock.tasks.recalculate_stock_level.delay"):
            resp = auth_client.post(url)
        assert resp.status_code == 200
        assert resp.json()["queued"] is True

    def test_scope_isolation(self, auth_client, stock_item_factory):
        """Items from other stores must not appear."""
        from orders.tests.factories import StoreFactory

        other_store = StoreFactory()
        stock_item_factory(name="Outro", store=other_store)
        url = reverse("stock-item-list")
        resp = auth_client.get(url)
        assert resp.status_code == 200
        assert len(resp.json()) == 0


class TestStockMovementAPI:
    def test_create_entrada(self, auth_client, stock_item_factory, store):
        item = stock_item_factory(store=store)
        url = reverse("stock-movement-list")
        payload = {
            "stock_item": str(item.id),
            "type": "ENTRADA",
            "quantity": "10.000",
            "notes": "Compra NF 123",
        }
        with patch("stock.tasks.recalculate_stock_level.delay"):
            resp = auth_client.post(url, payload, format="json")
        assert resp.status_code == 201
        assert resp.json()["type"] == "ENTRADA"

    def test_create_saida_normalizes_negative(self, auth_client, stock_item_factory, store):
        item = stock_item_factory(store=store)
        url = reverse("stock-movement-list")
        payload = {
            "stock_item": str(item.id),
            "type": "SAIDA",
            "quantity": "5.000",  # Positive, should be negated
            "notes": "Consumo manual",
        }
        with patch("stock.tasks.recalculate_stock_level.delay"):
            resp = auth_client.post(url, payload, format="json")
        assert resp.status_code == 201
        assert Decimal(resp.json()["quantity"]) == Decimal("-5.000")

    def test_list_movements(self, auth_client, stock_movement_factory, stock_item_factory, store):
        item = stock_item_factory(store=store)
        stock_movement_factory(stock_item=item)
        url = reverse("stock-movement-list")
        resp = auth_client.get(url)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_no_put_allowed(self, auth_client, stock_movement_factory, stock_item_factory, store):
        item = stock_item_factory(store=store)
        mov = stock_movement_factory(stock_item=item)
        url = reverse("stock-movement-detail", args=[str(mov.id)])
        resp = auth_client.put(url, {}, format="json")
        assert resp.status_code == 405

    def test_no_delete_allowed(self, auth_client, stock_movement_factory, stock_item_factory, store):
        item = stock_item_factory(store=store)
        mov = stock_movement_factory(stock_item=item)
        url = reverse("stock-movement-detail", args=[str(mov.id)])
        resp = auth_client.delete(url)
        assert resp.status_code == 405


class TestStockAlertAPI:
    def test_list_open_alerts(self, auth_client, stock_alert_factory, stock_item_factory, store):
        item = stock_item_factory(store=store)
        stock_alert_factory(stock_item=item, is_resolved=False)
        url = reverse("stock-alert-list")
        resp = auth_client.get(url)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_list_all_alerts_with_open_false(self, auth_client, stock_alert_factory, stock_item_factory, store):
        item1 = stock_item_factory(name="A", store=store)
        item2 = stock_item_factory(name="B", store=store)
        stock_alert_factory(stock_item=item1, is_resolved=False)
        stock_alert_factory(stock_item=item2, is_resolved=True)
        url = reverse("stock-alert-list")
        resp = auth_client.get(url + "?open=false")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_resolve_alert(self, auth_client, stock_alert_factory, stock_item_factory, store):
        item = stock_item_factory(store=store)
        alert = stock_alert_factory(stock_item=item, is_resolved=False)
        url = reverse("stock-alert-resolve", args=[str(alert.id)])
        resp = auth_client.post(url)
        assert resp.status_code == 200
        assert resp.json()["is_resolved"] is True
        assert resp.json()["resolved_at"] is not None

    def test_alert_read_only_no_post(self, auth_client):
        url = reverse("stock-alert-list")
        resp = auth_client.post(url, {}, format="json")
        assert resp.status_code == 405


class TestBillOfMaterialsAPI:
    def test_list_bom(self, auth_client, bom_factory, stock_item_factory, product_factory, store):
        item = stock_item_factory(store=store)
        product = product_factory()
        bom_factory(product=product, stock_item=item)
        url = reverse("stock-bom-list")
        resp = auth_client.get(url)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_create_bom(self, auth_client, stock_item_factory, product_factory, store):
        item = stock_item_factory(store=store)
        product = product_factory()
        url = reverse("stock-bom-list")
        payload = {
            "product": str(product.id),
            "stock_item": str(item.id),
            "quantity_per_unit": "0.250",
        }
        resp = auth_client.post(url, payload, format="json")
        assert resp.status_code == 201
        assert resp.json()["quantity_per_unit"] == "0.250"

    def test_patch_bom(self, auth_client, bom_factory, stock_item_factory, product_factory, store):
        item = stock_item_factory(store=store)
        product = product_factory()
        bom = bom_factory(product=product, stock_item=item, quantity_per_unit=Decimal("0.200"))
        url = reverse("stock-bom-detail", args=[str(bom.id)])
        resp = auth_client.patch(url, {"quantity_per_unit": "0.350"}, format="json")
        assert resp.status_code == 200
        assert resp.json()["quantity_per_unit"] == "0.350"

    def test_delete_bom(self, auth_client, bom_factory, stock_item_factory, product_factory, store):
        item = stock_item_factory(store=store)
        product = product_factory()
        bom = bom_factory(product=product, stock_item=item)
        url = reverse("stock-bom-detail", args=[str(bom.id)])
        resp = auth_client.delete(url)
        assert resp.status_code == 204
