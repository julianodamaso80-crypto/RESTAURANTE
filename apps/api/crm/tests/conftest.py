import pytest
from rest_framework.test import APIClient

from cdp.tests.factories import ConsentRecordFactory, CustomerFactory
from orders.tests.factories import CompanyFactory, StoreFactory, TenantFactory, UserFactory

from .factories import (
    CampaignFactory,
    CampaignRecipientFactory,
    CampaignRunFactory,
    CampaignTemplateFactory,
    CustomerSegmentFactory,
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
def tenant_factory(db):
    def _create(**kwargs):
        return TenantFactory(**kwargs)

    return _create


@pytest.fixture
def customer_factory(tenant):
    def _create(**kwargs):
        kwargs.setdefault("tenant", tenant)
        return CustomerFactory(**kwargs)

    return _create


@pytest.fixture
def segment_factory(tenant):
    def _create(**kwargs):
        kwargs.setdefault("tenant", tenant)
        return CustomerSegmentFactory(**kwargs)

    return _create


@pytest.fixture
def campaign_template_factory(tenant):
    def _create(**kwargs):
        kwargs.setdefault("tenant", tenant)
        return CampaignTemplateFactory(**kwargs)

    return _create


@pytest.fixture
def campaign_factory(store):
    def _create(**kwargs):
        kwargs.setdefault("store", store)
        kwargs.setdefault("tenant", store.company.tenant)
        if "segment" not in kwargs:
            kwargs["segment"] = CustomerSegmentFactory(tenant=kwargs["tenant"])
        if "template" not in kwargs:
            kwargs["template"] = CampaignTemplateFactory(tenant=kwargs["tenant"])
        return CampaignFactory(**kwargs)

    return _create


@pytest.fixture
def campaign_run_factory(store):
    def _create(**kwargs):
        if "campaign" not in kwargs:
            tenant = store.company.tenant
            kwargs["campaign"] = CampaignFactory(
                store=store,
                tenant=tenant,
                segment=CustomerSegmentFactory(tenant=tenant),
                template=CampaignTemplateFactory(tenant=tenant),
            )
        return CampaignRunFactory(**kwargs)

    return _create


@pytest.fixture
def campaign_recipient_factory(store):
    def _create(**kwargs):
        if "run" not in kwargs:
            tenant = store.company.tenant
            campaign = CampaignFactory(
                store=store,
                tenant=tenant,
                segment=CustomerSegmentFactory(tenant=tenant),
                template=CampaignTemplateFactory(tenant=tenant),
            )
            kwargs["run"] = CampaignRunFactory(campaign=campaign)
        if "customer" not in kwargs:
            tenant = kwargs["run"].campaign.tenant
            kwargs["customer"] = CustomerFactory(tenant=tenant)
        return CampaignRecipientFactory(**kwargs)

    return _create


@pytest.fixture
def consent_record_factory(customer_factory):
    def _create(**kwargs):
        if "customer" not in kwargs:
            kwargs["customer"] = customer_factory()
        return ConsentRecordFactory(**kwargs)

    return _create
