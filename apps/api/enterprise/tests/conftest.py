import pytest
from rest_framework.test import APIClient

from catalog.tests.factories import CatalogFactory, CategoryFactory, ProductFactory
from orders.tests.factories import CompanyFactory, StoreFactory, TenantFactory, UserFactory
from stock.tests.factories import StockAlertFactory, StockItemFactory

from .factories import (
    FranchiseeOnboardingFactory,
    FranchiseTemplateFactory,
    NetworkAlertFactory,
    NetworkReportFactory,
    StoreOverrideFactory,
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
def franchise_template_factory(company):
    def _create(**kwargs):
        kwargs.setdefault("company", company)
        return FranchiseTemplateFactory(**kwargs)

    return _create


@pytest.fixture
def store_override_factory(store, franchise_template_factory):
    def _create(**kwargs):
        kwargs.setdefault("store", store)
        if "template" not in kwargs:
            kwargs["template"] = franchise_template_factory()
        return StoreOverrideFactory(**kwargs)

    return _create


@pytest.fixture
def franchisee_onboarding_factory(franchise_template_factory):
    def _create(**kwargs):
        if "template" not in kwargs:
            kwargs["template"] = franchise_template_factory()
        if "store" not in kwargs:
            kwargs["store"] = StoreFactory(company=kwargs["template"].company)
        return FranchiseeOnboardingFactory(**kwargs)

    return _create


@pytest.fixture
def network_report_factory(company):
    def _create(**kwargs):
        kwargs.setdefault("company", company)
        return NetworkReportFactory(**kwargs)

    return _create


@pytest.fixture
def network_alert_factory(company, store):
    def _create(**kwargs):
        kwargs.setdefault("company", company)
        kwargs.setdefault("store", store)
        return NetworkAlertFactory(**kwargs)

    return _create


@pytest.fixture
def store_factory(company):
    def _create(**kwargs):
        kwargs.setdefault("company", company)
        return StoreFactory(**kwargs)

    return _create


@pytest.fixture
def company_factory(tenant):
    def _create(**kwargs):
        kwargs.setdefault("tenant", tenant)
        return CompanyFactory(**kwargs)

    return _create


@pytest.fixture
def product_factory(db):
    def _create(**kwargs):
        return ProductFactory(**kwargs)

    return _create


@pytest.fixture
def catalog_factory(db):
    def _create(**kwargs):
        return CatalogFactory(**kwargs)

    return _create


@pytest.fixture
def category_factory(db):
    def _create(**kwargs):
        return CategoryFactory(**kwargs)

    return _create


@pytest.fixture
def stock_item_factory(store):
    def _create(**kwargs):
        kwargs.setdefault("store", store)
        return StockItemFactory(**kwargs)

    return _create


@pytest.fixture
def stock_alert_factory(store):
    def _create(**kwargs):
        if "stock_item" not in kwargs:
            kwargs["stock_item"] = StockItemFactory(store=store)
        kwargs.setdefault("store", kwargs["stock_item"].store)
        return StockAlertFactory(**kwargs)

    return _create
