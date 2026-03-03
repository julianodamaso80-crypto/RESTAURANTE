from .enums import OrderStatus

# Valid transitions: from state X, can go to which states
VALID_TRANSITIONS = {
    OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
    OrderStatus.CONFIRMED: [OrderStatus.IN_PREPARATION, OrderStatus.CANCELLED],
    OrderStatus.IN_PREPARATION: [OrderStatus.READY, OrderStatus.CANCELLED],
    OrderStatus.READY: [OrderStatus.DISPATCHED, OrderStatus.DELIVERED, OrderStatus.CANCELLED],
    OrderStatus.DISPATCHED: [OrderStatus.DELIVERED, OrderStatus.CANCELLED],
    OrderStatus.DELIVERED: [],  # final state
    OrderStatus.CANCELLED: [],  # final state
}


class InvalidOrderTransition(Exception):
    """Raised when a state transition is invalid."""

    pass


def transition(order, new_status: str):
    """Apply state transition on order.

    Raises InvalidOrderTransition if the transition is not allowed.
    Does NOT save — caller's responsibility.
    """
    current = order.status
    allowed = VALID_TRANSITIONS.get(OrderStatus(current), [])

    try:
        target = OrderStatus(new_status)
    except ValueError:
        raise InvalidOrderTransition(f"Status '{new_status}' não é um status válido.")

    if target not in allowed:
        raise InvalidOrderTransition(
            f"Transição inválida: '{current}' → '{new_status}'. "
            f"Permitidas: {[s.value for s in allowed] or 'nenhuma (estado final)'}."
        )

    order.status = target
