import pytest

from kds.models import KDSTicket
from orders.enums import OrderStatus, OrderType


@pytest.mark.django_db
def test_ticket_created_on_order_confirmed(order_factory, kds_station_factory):
    """Signal creates KDSTicket when Order moves to CONFIRMED."""
    order = order_factory(status=OrderStatus.PENDING)
    station = kds_station_factory(store=order.store)

    order.transition_to(OrderStatus.CONFIRMED)
    order.save()

    assert KDSTicket.objects.filter(order=order, station=station).exists()


@pytest.mark.django_db
def test_ticket_creation_is_idempotent(order_factory, kds_station_factory):
    """Signal with get_or_create: confirming 2x does not create 2 tickets."""
    order = order_factory(status=OrderStatus.PENDING)
    station = kds_station_factory(store=order.store)

    order.transition_to(OrderStatus.CONFIRMED)
    order.save()
    order.save()  # second time — should not create duplicate

    assert KDSTicket.objects.filter(order=order, station=station).count() == 1


@pytest.mark.django_db
def test_ticket_respects_order_type_filter(order_factory, kds_station_factory):
    """Station with filter_order_types does not create ticket for different order_type."""
    order = order_factory(status=OrderStatus.PENDING, order_type=OrderType.TABLE)
    kds_station_factory(
        store=order.store,
        filter_order_types=[OrderType.DELIVERY],  # only delivery
    )

    order.transition_to(OrderStatus.CONFIRMED)
    order.save()

    # TABLE order should NOT create ticket at this DELIVERY-only station
    assert not KDSTicket.objects.filter(order=order).exists()


@pytest.mark.django_db
def test_ticket_not_created_for_pending_order(order_factory, kds_station_factory):
    """Signal does NOT fire for PENDING orders."""
    order = order_factory(status=OrderStatus.PENDING)
    kds_station_factory(store=order.store)

    order.save()  # still PENDING

    assert KDSTicket.objects.count() == 0


@pytest.mark.django_db
def test_ticket_created_for_multiple_stations(order_factory, kds_station_factory):
    """One confirmed order creates tickets on all active stations."""
    order = order_factory(status=OrderStatus.PENDING)
    kds_station_factory(store=order.store, name="Grill")
    kds_station_factory(store=order.store, name="Drinks")

    order.transition_to(OrderStatus.CONFIRMED)
    order.save()

    assert KDSTicket.objects.filter(order=order).count() == 2
