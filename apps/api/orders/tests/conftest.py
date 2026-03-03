import pytest
from rest_framework.test import APIClient

from .factories import CompanyFactory, OrderFactory, OrderItemFactory, StoreFactory, TenantFactory, UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def tenant(db):
    return TenantFactory()


@pytest.fixture
def company(tenant):
    return CompanyFactory(tenant=tenant)


@pytest.fixture
def store(company):
    return StoreFactory(company=company)


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def order_factory(store):
    def _create(**kwargs):
        kwargs.setdefault("store", store)
        kwargs.setdefault("tenant", store.company.tenant)
        return OrderFactory(**kwargs)

    return _create


@pytest.fixture
def order(order_factory):
    return order_factory()


@pytest.fixture
def order_item_factory(order):
    def _create(**kwargs):
        kwargs.setdefault("order", order)
        return OrderItemFactory(**kwargs)

    return _create
