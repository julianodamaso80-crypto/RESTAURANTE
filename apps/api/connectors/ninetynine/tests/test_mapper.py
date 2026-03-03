from connectors.ninetynine.mapper import map_ninetynine_order_to_internal
from orders.enums import OrderChannel, OrderType

SAMPLE_ORDER = {
    "id": "99food-order-001",
    "displayId": "#0099",
    "merchantId": "merchant-99-001",
    "subTotal": 42.90,
    "totalPrice": 49.90,
    "totalDiscount": 0.0,
    "delivery": {"mode": "DELIVERY", "deliveryFee": 7.00},
    "items": [
        {
            "id": "item-99-001",
            "externalCode": "SKU-Y",
            "name": "Combo 99",
            "quantity": 1,
            "unitPrice": 42.90,
            "totalPrice": 42.90,
            "observations": "sem pimenta",
        }
    ],
}


class FakeTenant:
    id = "tenant-001"


class FakeStore:
    id = "store-001"


def test_channel_is_ninetynine():
    result = map_ninetynine_order_to_internal(SAMPLE_ORDER, FakeTenant(), FakeStore())
    assert result["channel"] == OrderChannel.NINETYNINE


def test_converts_to_cents():
    result = map_ninetynine_order_to_internal(SAMPLE_ORDER, FakeTenant(), FakeStore())
    assert result["subtotal_cents"] == 4290
    assert result["total_cents"] == 4990
    assert result["delivery_fee_cents"] == 700


def test_maps_items():
    result = map_ninetynine_order_to_internal(SAMPLE_ORDER, FakeTenant(), FakeStore())
    assert len(result["items"]) == 1
    item = result["items"][0]
    assert item["name"] == "Combo 99"
    assert item["quantity"] == 1
    assert item["notes"] == "sem pimenta"


def test_external_id_and_display():
    result = map_ninetynine_order_to_internal(SAMPLE_ORDER, FakeTenant(), FakeStore())
    assert result["external_id"] == "99food-order-001"
    assert result["display_number"] == "#0099"


def test_mapper_isolado_do_connector():
    """Mapper does not import anything from auth or credentials."""
    import inspect

    from connectors.ninetynine import mapper

    source = inspect.getsource(mapper)
    assert "NinetyNineStoreCredential" not in source
    assert "access_token" not in source


def test_takeout_order_type():
    payload = {**SAMPLE_ORDER, "delivery": {"mode": "TAKEOUT", "deliveryFee": 0}}
    result = map_ninetynine_order_to_internal(payload, FakeTenant(), FakeStore())
    assert result["order_type"] == OrderType.TAKEOUT
    assert result["delivery_fee_cents"] == 0
