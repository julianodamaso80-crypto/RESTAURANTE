import pytest
from rest_framework.test import APIClient

from orders.tests.factories import CompanyFactory, StoreFactory, TenantFactory, UserFactory

from .factories import (
    CatalogFactory,
    CategoryFactory,
    ModifierGroupFactory,
    ModifierOptionFactory,
    ProductChannelMapFactory,
    ProductFactory,
)


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
def catalog_factory(store):
    def _create(**kwargs):
        kwargs.setdefault("tenant", store.company.tenant)
        kwargs.setdefault("company", store.company)
        kwargs.setdefault("store", store)
        return CatalogFactory(**kwargs)

    return _create


@pytest.fixture
def category_factory(catalog_factory):
    def _create(**kwargs):
        if "catalog" not in kwargs:
            kwargs["catalog"] = catalog_factory()
        return CategoryFactory(**kwargs)

    return _create


@pytest.fixture
def product_factory(category_factory):
    def _create(**kwargs):
        if "category" not in kwargs:
            kwargs["category"] = category_factory()
        return ProductFactory(**kwargs)

    return _create


@pytest.fixture
def modifier_group_factory(product_factory):
    def _create(**kwargs):
        if "product" not in kwargs:
            kwargs["product"] = product_factory()
        return ModifierGroupFactory(**kwargs)

    return _create


@pytest.fixture
def modifier_option_factory(modifier_group_factory):
    def _create(**kwargs):
        if "group" not in kwargs:
            kwargs["group"] = modifier_group_factory()
        return ModifierOptionFactory(**kwargs)

    return _create


@pytest.fixture
def product_channel_map_factory(product_factory):
    def _create(**kwargs):
        if "product" not in kwargs:
            kwargs["product"] = product_factory()
        return ProductChannelMapFactory(**kwargs)

    return _create
