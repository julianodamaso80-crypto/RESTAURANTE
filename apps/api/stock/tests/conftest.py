import pytest
from rest_framework.test import APIClient

from catalog.tests.factories import ProductChannelMapFactory, ProductFactory
from orders.tests.factories import (
    CompanyFactory,
    OrderFactory,
    OrderItemFactory,
    StoreFactory,
    TenantFactory,
    UserFactory,
)

from .factories import (
    BillOfMaterialsFactory,
    StockAlertFactory,
    StockItemFactory,
    StockLevelFactory,
    StockMovementFactory,
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
def stock_item_factory(store):
    def _create(**kwargs):
        kwargs.setdefault("store", store)
        return StockItemFactory(**kwargs)

    return _create


@pytest.fixture
def stock_movement_factory(store):
    def _create(**kwargs):
        if "stock_item" not in kwargs:
            kwargs["stock_item"] = StockItemFactory(store=store)
        kwargs.setdefault("store", store)
        return StockMovementFactory(**kwargs)

    return _create


@pytest.fixture
def stock_level_factory(store):
    def _create(**kwargs):
        if "stock_item" not in kwargs:
            kwargs["stock_item"] = StockItemFactory(store=store)
        return StockLevelFactory(**kwargs)

    return _create


@pytest.fixture
def stock_alert_factory(store):
    def _create(**kwargs):
        if "stock_item" not in kwargs:
            kwargs["stock_item"] = StockItemFactory(store=store)
        kwargs.setdefault("store", kwargs["stock_item"].store)
        return StockAlertFactory(**kwargs)

    return _create


@pytest.fixture
def bom_factory(store):
    def _create(**kwargs):
        if "stock_item" not in kwargs:
            kwargs["stock_item"] = StockItemFactory(store=store)
        return BillOfMaterialsFactory(**kwargs)

    return _create


@pytest.fixture
def product_factory(db):
    def _create(**kwargs):
        return ProductFactory(**kwargs)

    return _create


@pytest.fixture
def product_channel_map_factory(db):
    def _create(**kwargs):
        return ProductChannelMapFactory(**kwargs)

    return _create


@pytest.fixture
def order_factory(store):
    def _create(**kwargs):
        kwargs.setdefault("store", store)
        kwargs.setdefault("tenant", store.company.tenant)
        return OrderFactory(**kwargs)

    return _create


@pytest.fixture
def order_item_factory(db):
    def _create(**kwargs):
        return OrderItemFactory(**kwargs)

    return _create
