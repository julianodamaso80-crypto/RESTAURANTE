import inspect

import pytest
from django.db import IntegrityError

from orders.enums import OrderStatus
from orders.models import IdempotencyKey


@pytest.mark.django_db
def test_order_creation(order_factory):
    order = order_factory()
    assert order.pk is not None
    assert order.status == OrderStatus.PENDING


@pytest.mark.django_db
def test_order_transition_saves_timestamp(order_factory):
    order = order_factory()
    assert order.confirmed_at is None
    order.transition_to(OrderStatus.CONFIRMED)
    order.save()
    order.refresh_from_db()
    assert order.confirmed_at is not None


@pytest.mark.django_db
def test_idempotency_key_unique_per_tenant(order_factory):
    order = order_factory()
    IdempotencyKey.objects.create(tenant=order.tenant, key="evt-123", order=order)
    with pytest.raises(IntegrityError):
        IdempotencyKey.objects.create(tenant=order.tenant, key="evt-123", order=order)


@pytest.mark.django_db
def test_order_has_no_external_dependency():
    import orders.models as m

    source = inspect.getsource(m)
    assert "ifood" not in source.lower()
    assert "99food" not in source.lower()
    assert "celery" not in source.lower()
