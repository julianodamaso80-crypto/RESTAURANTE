import pytest

from .factories import RappiRawEventFactory, RappiStoreCredentialFactory


@pytest.fixture
def raw_event_factory(db):
    def _create(**kwargs):
        return RappiRawEventFactory(**kwargs)

    return _create


@pytest.fixture
def raw_event(raw_event_factory):
    return raw_event_factory()


@pytest.fixture
def tenant_factory(db):
    from orders.tests.factories import TenantFactory

    def _create(**kwargs):
        return TenantFactory(**kwargs)

    return _create


@pytest.fixture
def store_factory(db):
    from orders.tests.factories import StoreFactory

    def _create(**kwargs):
        store = StoreFactory(**kwargs)
        RappiStoreCredentialFactory(store=store)
        return store

    return _create


@pytest.fixture
def order_factory(db):
    from orders.tests.factories import OrderFactory

    def _create(**kwargs):
        return OrderFactory(**kwargs)

    return _create
