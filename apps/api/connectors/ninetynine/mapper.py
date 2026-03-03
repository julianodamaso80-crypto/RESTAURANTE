from orders.enums import OrderChannel, OrderType


def map_ninetynine_order_to_internal(payload: dict, tenant, store) -> dict:
    """Map Open Delivery payload (99Food) to internal Order dict.

    Does NOT persist anything — pure transformation.

    Open Delivery uses the same fields as iFood v2:
    - id, displayId, merchantId
    - delivery.mode (DELIVERY | TAKEOUT)
    - items[].name, quantity, unitPrice, totalPrice
    - totalPrice, subTotal, totalDiscount
    """
    order_data = payload.get("order", payload)

    delivery_method = order_data.get("delivery", {}).get("mode", "DELIVERY")
    order_type_map = {
        "DELIVERY": OrderType.DELIVERY,
        "TAKEOUT": OrderType.TAKEOUT,
        "DEFAULT": OrderType.DELIVERY,
    }
    order_type = order_type_map.get(delivery_method, OrderType.DELIVERY)

    def to_cents(value) -> int:
        try:
            return int(round(float(value) * 100))
        except (TypeError, ValueError):
            return 0

    total_price = order_data.get("totalPrice", 0)
    sub_total = order_data.get("subTotal", total_price)
    delivery_fee = order_data.get("delivery", {}).get("deliveryFee", 0)

    items = []
    for item in order_data.get("items", []):
        items.append({
            "name": item.get("name", "Item"),
            "external_item_id": item.get("externalCode") or item.get("id", ""),
            "quantity": int(item.get("quantity", 1)),
            "unit_price_cents": to_cents(item.get("unitPrice", 0)),
            "total_cents": to_cents(item.get("totalPrice", 0)),
            "notes": item.get("observations", ""),
        })

    external_id = order_data.get("id") or order_data.get("orderId", "")
    display_number = order_data.get("displayId") or order_data.get("shortReference", external_id[:8])

    return {
        "tenant": tenant,
        "store": store,
        "channel": OrderChannel.NINETYNINE,
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
