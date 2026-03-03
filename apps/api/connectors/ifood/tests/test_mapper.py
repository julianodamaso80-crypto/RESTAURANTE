from connectors.ifood.mapper import map_ifood_order_to_internal
from orders.enums import OrderChannel, OrderType

SAMPLE_IFOOD_ORDER = {
    "id": "ifood-order-001",
    "displayId": "#0042",
    "merchantId": "merchant-001",
    "subTotal": 35.90,
    "totalPrice": 41.90,
    "totalDiscount": 0.0,
    "delivery": {
        "mode": "DELIVERY",
        "deliveryFee": 6.00,
    },
    "items": [
        {
            "id": "item-001",
            "externalCode": "SKU-X",
            "name": "X-Burguer",
            "quantity": 2,
            "unitPrice": 17.95,
            "totalPrice": 35.90,
            "observations": "sem cebola",
        }
    ],
    "observations": "",
}


class FakeTenant:
    id = "tenant-001"


class FakeStore:
    id = "store-001"


def test_mapper_channel_is_ifood():
    result = map_ifood_order_to_internal(SAMPLE_IFOOD_ORDER, FakeTenant(), FakeStore())
    assert result["channel"] == OrderChannel.IFOOD


def test_mapper_order_type_delivery():
    result = map_ifood_order_to_internal(SAMPLE_IFOOD_ORDER, FakeTenant(), FakeStore())
    assert result["order_type"] == OrderType.DELIVERY


def test_mapper_converts_to_cents():
    result = map_ifood_order_to_internal(SAMPLE_IFOOD_ORDER, FakeTenant(), FakeStore())
    assert result["subtotal_cents"] == 3590
    assert result["total_cents"] == 4190
    assert result["delivery_fee_cents"] == 600


def test_mapper_items():
    result = map_ifood_order_to_internal(SAMPLE_IFOOD_ORDER, FakeTenant(), FakeStore())
    assert len(result["items"]) == 1
    item = result["items"][0]
    assert item["name"] == "X-Burguer"
    assert item["quantity"] == 2
    assert item["unit_price_cents"] == 1795
    assert item["notes"] == "sem cebola"


def test_mapper_external_id():
    result = map_ifood_order_to_internal(SAMPLE_IFOOD_ORDER, FakeTenant(), FakeStore())
    assert result["external_id"] == "ifood-order-001"
    assert result["display_number"] == "#0042"


def test_mapper_takeout():
    payload = {**SAMPLE_IFOOD_ORDER, "delivery": {"mode": "TAKEOUT", "deliveryFee": 0}}
    result = map_ifood_order_to_internal(payload, FakeTenant(), FakeStore())
    assert result["order_type"] == OrderType.TAKEOUT


def test_mapper_no_core_imports():
    """Ensures mapper does not import any iFood-specific models in the orders core."""
    import inspect

    from connectors.ifood import mapper

    source = inspect.getsource(mapper)
    assert "ifood_credential" not in source.lower()
    assert "RawEvent" not in source
