import pytest

from orders.enums import OrderStatus
from orders.fsm import InvalidOrderTransition, transition


class FakeOrder:
    def __init__(self, status):
        self.status = status


VALID = [
    (OrderStatus.PENDING, OrderStatus.CONFIRMED),
    (OrderStatus.PENDING, OrderStatus.CANCELLED),
    (OrderStatus.CONFIRMED, OrderStatus.IN_PREPARATION),
    (OrderStatus.CONFIRMED, OrderStatus.CANCELLED),
    (OrderStatus.IN_PREPARATION, OrderStatus.READY),
    (OrderStatus.IN_PREPARATION, OrderStatus.CANCELLED),
    (OrderStatus.READY, OrderStatus.DISPATCHED),
    (OrderStatus.READY, OrderStatus.DELIVERED),
    (OrderStatus.READY, OrderStatus.CANCELLED),
    (OrderStatus.DISPATCHED, OrderStatus.DELIVERED),
    (OrderStatus.DISPATCHED, OrderStatus.CANCELLED),
]

INVALID = [
    (OrderStatus.PENDING, OrderStatus.IN_PREPARATION),
    (OrderStatus.PENDING, OrderStatus.DELIVERED),
    (OrderStatus.CONFIRMED, OrderStatus.DELIVERED),
    (OrderStatus.CONFIRMED, OrderStatus.DISPATCHED),
    (OrderStatus.DELIVERED, OrderStatus.CANCELLED),
    (OrderStatus.DELIVERED, OrderStatus.PENDING),
    (OrderStatus.CANCELLED, OrderStatus.CONFIRMED),
    (OrderStatus.CANCELLED, OrderStatus.PENDING),
]


@pytest.mark.parametrize("from_status,to_status", VALID)
def test_valid_transition(from_status, to_status):
    order = FakeOrder(from_status)
    transition(order, to_status)
    assert order.status == to_status


@pytest.mark.parametrize("from_status,to_status", INVALID)
def test_invalid_transition_raises(from_status, to_status):
    order = FakeOrder(from_status)
    with pytest.raises(InvalidOrderTransition):
        transition(order, to_status)


def test_invalid_status_string_raises():
    order = FakeOrder(OrderStatus.PENDING)
    with pytest.raises(InvalidOrderTransition):
        transition(order, "STATUS_QUE_NAO_EXISTE")


def test_final_state_has_no_transitions():
    for final in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
        order = FakeOrder(final)
        with pytest.raises(InvalidOrderTransition):
            transition(order, OrderStatus.PENDING)
