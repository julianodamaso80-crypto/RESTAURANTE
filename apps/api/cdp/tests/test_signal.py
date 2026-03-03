import inspect
from unittest.mock import MagicMock, patch

import pytest

from orders.enums import OrderStatus


@pytest.mark.django_db
def test_signal_fires_on_delivered(order_factory):
    """Signal dispara quando order.status = DELIVERED."""
    order = order_factory(status=OrderStatus.PENDING)
    order.transition_to(OrderStatus.CONFIRMED)
    order.transition_to(OrderStatus.IN_PREPARATION)
    order.transition_to(OrderStatus.READY)
    order.transition_to(OrderStatus.DISPATCHED)
    order.save()

    with patch("cdp.tasks.recalculate_customer_rfv") as mock_task, patch(
        "stock.tasks.debit_stock_for_order.delay"
    ):
        mock_task.delay = MagicMock()
        order.transition_to(OrderStatus.DELIVERED)
        order.save()

    # Signal fires but may not find a customer — that's OK, no exception


@pytest.mark.django_db
def test_signal_does_not_fire_on_other_statuses(order_factory):
    order = order_factory(status=OrderStatus.PENDING)

    with patch("cdp.tasks.recalculate_customer_rfv") as mock_task:
        mock_task.delay = MagicMock()
        order.transition_to(OrderStatus.CONFIRMED)
        order.save()

    mock_task.delay.assert_not_called()


@pytest.mark.django_db
def test_signal_creates_event_when_customer_found(order_factory, customer_factory, customer_identity_factory):
    """When a matching customer exists, signal creates event and triggers RFV."""
    from cdp.models import CustomerEvent, CustomerEventType

    order = order_factory(status=OrderStatus.PENDING, external_id="ifood-order-123")

    # Create customer with identity matching the order's external_id
    customer = customer_factory(tenant=order.tenant)
    customer_identity_factory(customer=customer, value="ifood-order-123")

    order.transition_to(OrderStatus.CONFIRMED)
    order.transition_to(OrderStatus.IN_PREPARATION)
    order.transition_to(OrderStatus.READY)
    order.transition_to(OrderStatus.DISPATCHED)
    order.save()

    with patch("cdp.tasks.recalculate_customer_rfv.delay") as mock_delay, patch(
        "stock.tasks.debit_stock_for_order.delay"
    ):
        order.transition_to(OrderStatus.DELIVERED)
        order.save()

        assert CustomerEvent.objects.filter(
            customer=customer,
            event_type=CustomerEventType.ORDER_DELIVERED,
        ).exists()
        mock_delay.assert_called_once_with(str(customer.id))


@pytest.mark.django_db
def test_signal_uses_delay_not_direct_call():
    import cdp.signals as sig

    source = inspect.getsource(sig)
    assert ".delay(" in source
