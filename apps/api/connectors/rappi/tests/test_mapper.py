from connectors.rappi.mapper import map_rappi_order_to_internal
from orders.enums import OrderChannel, OrderType

SAMPLE_ORDER = {
    "id": "rappi-order-001",
    "displayId": "#R0099",
    "store_id": "rappi-store-001",
    "subTotal": 42.90,
    "totalPrice": 49.90,
    "totalDiscount": 0.0,
    "delivery": {"mode": "DELIVERY", "deliveryFee": 7.00},
    "items": [
        {
            "id": "item-rappi-001",
            "externalCode": "SKU-R",
            "name": "X-Burger Rappi",
            "quantity": 1,
            "unitPrice": 42.90,
            "totalPrice": 42.90,
            "observations": "sem cebola",
        }
    ],
}


class FakeTenant:
    id = "tenant-001"


class FakeStore:
    id = "store-001"


def test_channel_is_rappi():
    result = map_rappi_order_to_internal(SAMPLE_ORDER, FakeTenant(), FakeStore())
    assert result["channel"] == OrderChannel.RAPPI


def test_converts_to_cents():
    result = map_rappi_order_to_internal(SAMPLE_ORDER, FakeTenant(), FakeStore())
    assert result["subtotal_cents"] == 4290
    assert result["total_cents"] == 4990
    assert result["delivery_fee_cents"] == 700


def test_maps_items():
    result = map_rappi_order_to_internal(SAMPLE_ORDER, FakeTenant(), FakeStore())
    assert len(result["items"]) == 1
    item = result["items"][0]
    assert item["name"] == "X-Burger Rappi"
    assert item["quantity"] == 1
    assert item["notes"] == "sem cebola"


def test_external_id_and_display():
    result = map_rappi_order_to_internal(SAMPLE_ORDER, FakeTenant(), FakeStore())
    assert result["external_id"] == "rappi-order-001"
    assert result["display_number"] == "#R0099"


def test_mapper_isolado_do_connector():
    """Mapper does not import anything from auth or credentials."""
    import inspect

    from connectors.rappi import mapper

    source = inspect.getsource(mapper)
    assert "RappiStoreCredential" not in source
    assert "rappi_token" not in source


def test_takeout_order_type():
    payload = {**SAMPLE_ORDER, "delivery": {"mode": "TAKEOUT", "deliveryFee": 0}}
    result = map_rappi_order_to_internal(payload, FakeTenant(), FakeStore())
    assert result["order_type"] == OrderType.TAKEOUT
    assert result["delivery_fee_cents"] == 0
