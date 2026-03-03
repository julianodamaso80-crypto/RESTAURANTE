import pytest

from connectors.ifood.models import RawEventStatus


@pytest.mark.django_db
def test_nonexistent_raw_event_does_not_crash():
    from connectors.ninetynine.tasks import process_ninetynine_event

    process_ninetynine_event("00000000-0000-0000-0000-000000000000")


@pytest.mark.django_db
def test_non_order_event_marked_processed(raw_event_factory):
    from connectors.ninetynine.tasks import process_ninetynine_event

    raw_event = raw_event_factory(source="99food", event_type="STATUS_UPDATE", event_id="evt-99-status")
    process_ninetynine_event(str(raw_event.id))
    raw_event.refresh_from_db()
    assert raw_event.status == RawEventStatus.PROCESSED


@pytest.mark.django_db
def test_duplicate_event_marked_duplicate(raw_event_factory, order_factory, store_factory):
    from connectors.ninetynine.tasks import process_ninetynine_event
    from orders.models import IdempotencyKey

    store = store_factory()
    order = order_factory(store=store)

    IdempotencyKey.objects.create(
        tenant=store.company.tenant,
        key="99food:evt-99-dup-001",
        order=order,
    )

    raw_event = raw_event_factory(
        source="99food",
        event_id="evt-99-dup-001",
        event_type="PLACED",
        payload={"merchantId": store.ninetynine_credential.merchant_id, "orderId": "order-001"},
    )

    process_ninetynine_event(str(raw_event.id))

    raw_event.refresh_from_db()
    assert raw_event.status == RawEventStatus.DUPLICATE
