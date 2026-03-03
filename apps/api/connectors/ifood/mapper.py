from orders.enums import OrderChannel, OrderType


def map_ifood_order_to_internal(
    ifood_payload: dict,
    tenant,
    store,
) -> dict:
    """Map iFood payload to the internal Order schema.

    Returns a dict with fields ready for Order.objects.create().
    Does NOT persist anything — only transforms.
    """
    order_data = ifood_payload.get("order", ifood_payload)

    # Order type
    delivery_method = order_data.get("delivery", {}).get("mode", "DELIVERY")
    order_type_map = {
        "DELIVERY": OrderType.DELIVERY,
        "TAKEOUT": OrderType.TAKEOUT,
        "DEFAULT": OrderType.DELIVERY,
    }
    order_type = order_type_map.get(delivery_method, OrderType.DELIVERY)

    # Values (iFood sends monetary units, convert to cents)
    total_price = order_data.get("totalPrice", 0)
    sub_total = order_data.get("subTotal", total_price)
    delivery_fee = order_data.get("delivery", {}).get("deliveryFee", 0)

    def to_cents(value) -> int:
        """Convert float/string reais to integer cents."""
        try:
            return int(round(float(value) * 100))
        except (TypeError, ValueError):
            return 0

    # Items
    items = []
    for item in order_data.get("items", []):
        items.append(
            {
                "name": item.get("name", "Item"),
                "external_item_id": item.get("externalCode") or item.get("id", ""),
                "quantity": int(item.get("quantity", 1)),
                "unit_price_cents": to_cents(item.get("unitPrice", 0)),
                "total_cents": to_cents(item.get("totalPrice", 0)),
                "notes": item.get("observations", ""),
            }
        )

    external_id = order_data.get("id") or order_data.get("orderId", "")
    display_number = order_data.get("displayId") or order_data.get("shortReference", external_id[:8])

    return {
        "tenant": tenant,
        "store": store,
        "channel": OrderChannel.IFOOD,
        "order_type": order_type,
        "external_id": external_id,
        "display_number": display_number,
        "subtotal_cents": to_cents(sub_total),
        "delivery_fee_cents": to_cents(delivery_fee),
        "discount_cents": to_cents(order_data.get("totalDiscount", 0)),
        "total_cents": to_cents(total_price),
        "notes": order_data.get("observations", ""),
        "items": items,
    }
