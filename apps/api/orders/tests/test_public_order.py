import pytest
from rest_framework import status
from rest_framework.test import APIClient

from catalog.tests.factories import CatalogFactory, CategoryFactory, ProductFactory
from orders.enums import OrderChannel, OrderStatus, OrderType, PaymentMethod
from orders.models import Order


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def catalog(db):
    return CatalogFactory()


@pytest.fixture
def product(catalog):
    category = CategoryFactory(catalog=catalog)
    return ProductFactory(category=category, price_cents=2500)


BASE_PAYLOAD = {
    "customer_name": "João Silva",
    "customer_phone": "11999998888",
    "customer_email": "joao@example.com",
    "order_type": OrderType.TAKEOUT,
    "payment_method": PaymentMethod.PIX,
    "notes": "Sem cebola",
    "items": [
        {
            "name": "X-Burguer",
            "quantity": 2,
            "unit_price_cents": 2500,
            "total_cents": 5000,
            "notes": "",
        }
    ],
}


@pytest.mark.django_db
class TestPublicOrderCreate:
    url = "/api/v1/orders/public/"

    def _payload(self, catalog_id, **overrides):
        data = {**BASE_PAYLOAD, "catalog_id": str(catalog_id)}
        data.update(overrides)
        return data

    def test_create_takeout_order(self, api_client, catalog, product):
        resp = api_client.post(self.url, self._payload(catalog.id), format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["channel"] == OrderChannel.OWN
        assert data["order_type"] == OrderType.TAKEOUT
        assert data["status"] == OrderStatus.PENDING
        assert data["customer_name"] == "João Silva"
        assert data["subtotal_cents"] == 5000
        assert data["total_cents"] == 5000
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "X-Burguer"
        assert data["items"][0]["quantity"] == 2

    def test_create_delivery_order_with_address(self, api_client, catalog, product):
        address = {
            "street": "Rua A", "number": "100", "neighborhood": "Centro",
            "complement": "", "zipcode": "01000-000",
        }
        resp = api_client.post(
            self.url,
            self._payload(catalog.id, order_type=OrderType.DELIVERY, delivery_address=address),
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["order_type"] == OrderType.DELIVERY

    def test_delivery_without_address_fails(self, api_client, catalog, product):
        resp = api_client.post(
            self.url,
            self._payload(catalog.id, order_type=OrderType.DELIVERY),
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_empty_items_fails(self, api_client, catalog):
        resp = api_client.post(self.url, self._payload(catalog.id, items=[]), format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_customer_name_fails(self, api_client, catalog):
        payload = self._payload(catalog.id)
        del payload["customer_name"]
        resp = api_client.post(self.url, payload, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_catalog_fails(self, api_client, db):
        import uuid

        resp = api_client.post(self.url, self._payload(uuid.uuid4()), format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_cash_with_change(self, api_client, catalog, product):
        resp = api_client.post(
            self.url,
            self._payload(catalog.id, payment_method=PaymentMethod.CASH, change_for_cents=10000),
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED

    def test_idempotency_key(self, api_client, catalog, product):
        payload = self._payload(catalog.id, idempotency_key="own:abc123")
        resp1 = api_client.post(self.url, payload, format="json")
        resp2 = api_client.post(self.url, payload, format="json")
        assert resp1.status_code == status.HTTP_201_CREATED
        assert resp2.status_code == status.HTTP_201_CREATED
        assert resp1.json()["id"] == resp2.json()["id"]
        assert Order.objects.count() == 1

    def test_modifiers_summary_stored_in_notes(self, api_client, catalog, product):
        items = [
            {
                "name": "X-Burguer",
                "quantity": 1,
                "unit_price_cents": 2500,
                "total_cents": 2500,
                "notes": "Sem cebola",
                "modifiers_summary": "Ponto: Mal passado, Extra: Bacon",
            }
        ]
        resp = api_client.post(self.url, self._payload(catalog.id, items=items), format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        item = resp.json()["items"][0]
        assert "Ponto: Mal passado" in item["notes"]
        assert "Sem cebola" in item["notes"]


@pytest.mark.django_db
class TestPublicOrderDetail:
    def test_get_order(self, api_client, catalog, product):
        # Create order first
        create_url = "/api/v1/orders/public/"
        payload = {**BASE_PAYLOAD, "catalog_id": str(catalog.id)}
        resp = api_client.post(create_url, payload, format="json")
        order_id = resp.json()["id"]

        # Retrieve
        resp = api_client.get(f"/api/v1/orders/public/{order_id}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["id"] == order_id
        assert resp.json()["display_number"].startswith("#")

    def test_nonexistent_order_404(self, api_client, db):
        import uuid

        resp = api_client.get(f"/api/v1/orders/public/{uuid.uuid4()}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
