from unittest.mock import patch

import pytest

from connectors.ifood.models import RawEventStatus


@pytest.mark.django_db
def test_process_nonexistent_raw_event_does_not_crash():
    from connectors.ifood.tasks import process_ifood_event

    # Should not raise
    process_ifood_event("00000000-0000-0000-0000-000000000000")


@pytest.mark.django_db
def test_non_order_event_marked_processed(raw_event_factory):
    from connectors.ifood.tasks import process_ifood_event

    raw_event = raw_event_factory(event_type="STATUS_UPDATE", event_id="evt-status-1")
    process_ifood_event(str(raw_event.id))
    raw_event.refresh_from_db()
    assert raw_event.status == RawEventStatus.PROCESSED


@pytest.mark.django_db
def test_duplicate_event_marked_duplicate(raw_event_factory, order_factory, store_factory):
    """Same event_id processed 2x -> second time becomes DUPLICATE."""
    from connectors.ifood.tasks import process_ifood_event
    from orders.models import IdempotencyKey

    store = store_factory()
    order = order_factory(store=store, tenant=store.company.tenant)

    # Create idempotency key simulating first processing
    IdempotencyKey.objects.create(
        tenant=store.company.tenant,
        key="ifood:evt-dup-001",
        order=order,
    )

    raw_event = raw_event_factory(
        event_id="evt-dup-001",
        event_type="PLACED",
        payload={"merchantId": store.ifood_credential.merchant_id, "orderId": "ord-001"},
    )

    with patch("connectors.ifood.tasks._resolve_store", return_value=store):
        process_ifood_event(str(raw_event.id))

    raw_event.refresh_from_db()
    assert raw_event.status == RawEventStatus.DUPLICATE
