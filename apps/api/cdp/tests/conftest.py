import pytest
from rest_framework.test import APIClient

from orders.tests.factories import CompanyFactory, OrderFactory, StoreFactory, TenantFactory, UserFactory

from .factories import ConsentRecordFactory, CustomerEventFactory, CustomerFactory, CustomerIdentityFactory


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
def other_store(db):
    return StoreFactory()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, user, store):
    """Authenticated client with scope headers for the store."""
    api_client.force_authenticate(user=user)
    original_get = api_client.get
    original_post = api_client.post
    original_patch = api_client.patch
    original_delete = api_client.delete

    def _with_scope(method):
        def wrapper(*args, **kwargs):
            kwargs.setdefault("HTTP_X_STORE_ID", str(store.id))
            return method(*args, **kwargs)

        return wrapper

    api_client.get = _with_scope(original_get)
    api_client.post = _with_scope(original_post)
    api_client.patch = _with_scope(original_patch)
    api_client.delete = _with_scope(original_delete)
    return api_client


@pytest.fixture
def other_tenant(db):
    return TenantFactory()


@pytest.fixture
def customer_factory(tenant):
    def _create(**kwargs):
        kwargs.setdefault("tenant", tenant)
        return CustomerFactory(**kwargs)

    return _create


@pytest.fixture
def customer_identity_factory(customer_factory):
    def _create(**kwargs):
        if "customer" not in kwargs:
            kwargs["customer"] = customer_factory()
        return CustomerIdentityFactory(**kwargs)

    return _create


@pytest.fixture
def consent_record_factory(customer_factory):
    def _create(**kwargs):
        if "customer" not in kwargs:
            kwargs["customer"] = customer_factory()
        return ConsentRecordFactory(**kwargs)

    return _create


@pytest.fixture
def customer_event_factory(customer_factory):
    def _create(**kwargs):
        if "customer" not in kwargs:
            kwargs["customer"] = customer_factory()
        return CustomerEventFactory(**kwargs)

    return _create


@pytest.fixture
def order_factory(store):
    def _create(**kwargs):
        kwargs.setdefault("store", store)
        kwargs.setdefault("tenant", store.company.tenant)
        return OrderFactory(**kwargs)

    return _create
