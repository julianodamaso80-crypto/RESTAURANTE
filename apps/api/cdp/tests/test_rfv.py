import inspect

import pytest

from cdp.tasks import recalculate_customer_rfv


@pytest.mark.django_db
def test_rfv_no_orders_does_not_crash(customer_factory):
    c = customer_factory()
    # Deve completar sem erro mesmo sem orders
    recalculate_customer_rfv(str(c.id))


@pytest.mark.django_db
def test_rfv_nonexistent_customer_does_not_crash():
    # ID que não existe
    recalculate_customer_rfv("00000000-0000-0000-0000-000000000000")


@pytest.mark.django_db
def test_rfv_task_is_registered():
    from config.celery import app

    assert "cdp.tasks.recalculate_customer_rfv" in app.tasks


@pytest.mark.django_db
def test_rfv_no_orders_keeps_calculated_at_none(customer_factory):
    """Sem orders, rfv_calculated_at permanece None."""
    c = customer_factory()
    assert c.rfv_calculated_at is None
    recalculate_customer_rfv(str(c.id))
    c.refresh_from_db()
    # Task returns early when no orders — rfv_calculated_at stays None
    assert c.rfv_calculated_at is None


@pytest.mark.django_db
def test_rfv_with_matching_orders(customer_factory, order_factory):
    """RFV is calculated when matching orders exist."""
    from unittest.mock import patch

    from orders.enums import OrderStatus

    c = customer_factory(phone="+5511999990000")
    # Create delivered order with customer phone in notes
    order = order_factory(
        status=OrderStatus.PENDING,
        notes="Customer: +5511999990000",
        total_cents=5000,
    )
    order.transition_to(OrderStatus.CONFIRMED)
    order.transition_to(OrderStatus.IN_PREPARATION)
    order.transition_to(OrderStatus.READY)
    order.transition_to(OrderStatus.DISPATCHED)
    with patch("stock.tasks.debit_stock_for_order.delay"):
        order.transition_to(OrderStatus.DELIVERED)
        order.save()

    # Make customer belong to same tenant as order
    c.tenant = order.tenant
    c.save()

    recalculate_customer_rfv(str(c.id))
    c.refresh_from_db()

    assert c.rfv_frequency == 1
    assert c.rfv_monetary_cents == 5000
    assert c.rfv_recency_days is not None
    assert c.rfv_calculated_at is not None


@pytest.mark.django_db
def test_rfv_never_called_synchronously_in_signal():
    """Garante que o signal usa .delay() e não chama a task diretamente."""
    import cdp.signals as sig

    source = inspect.getsource(sig)
    assert ".delay(" in source
    # Should not have a direct call without .delay
    assert "recalculate_customer_rfv(" not in source.replace("recalculate_customer_rfv.delay(", "")
