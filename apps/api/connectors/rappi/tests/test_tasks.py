import pytest

from connectors.ifood.models import RawEventStatus


@pytest.mark.django_db
def test_nonexistent_raw_event_does_not_crash():
    from connectors.rappi.tasks import process_rappi_event

    process_rappi_event("00000000-0000-0000-0000-000000000000")


@pytest.mark.django_db
def test_non_order_event_marked_processed(raw_event_factory):
    from connectors.rappi.tasks import process_rappi_event

    raw_event = raw_event_factory(source="rappi", event_type="ORDER_STATUS_CHANGED", event_id="evt-rappi-status")
    process_rappi_event(str(raw_event.id))
    raw_event.refresh_from_db()
    assert raw_event.status == RawEventStatus.PROCESSED


@pytest.mark.django_db
def test_duplicate_event_marked_duplicate(raw_event_factory, order_factory, store_factory):
    from connectors.rappi.tasks import process_rappi_event
    from orders.models import IdempotencyKey

    store = store_factory()
    order = order_factory(store=store)

    IdempotencyKey.objects.create(
        tenant=store.company.tenant,
        key="rappi:evt-rappi-dup-001",
        order=order,
    )

    raw_event = raw_event_factory(
        source="rappi",
        event_id="evt-rappi-dup-001",
        event_type="NEW_ORDER",
        payload={"store_id": store.rappi_credential.rappi_store_id, "orderId": "order-001"},
    )

    process_rappi_event(str(raw_event.id))

    raw_event.refresh_from_db()
    assert raw_event.status == RawEventStatus.DUPLICATE
