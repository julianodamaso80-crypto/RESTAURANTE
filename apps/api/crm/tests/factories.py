import factory
from factory.django import DjangoModelFactory

from cdp.tests.factories import CustomerFactory
from crm.models import (
    Campaign,
    CampaignRecipient,
    CampaignRun,
    CampaignStatus,
    CampaignTemplate,
    CustomerSegment,
    RecipientStatus,
)
from orders.tests.factories import StoreFactory, TenantFactory


class CustomerSegmentFactory(DjangoModelFactory):
    class Meta:
        model = CustomerSegment

    tenant = factory.SubFactory(TenantFactory)
    name = factory.Sequence(lambda n: f"Segment {n}")
    description = "Test segment"
    criteria = factory.LazyFunction(lambda: [{"criteria": "ALL_CUSTOMERS", "value": None}])


class CampaignTemplateFactory(DjangoModelFactory):
    class Meta:
        model = CampaignTemplate

    tenant = factory.SubFactory(TenantFactory)
    name = factory.Sequence(lambda n: f"Template {n}")
    channel = "WHATSAPP"
    body = "Oi {{name}}, temos uma oferta especial!"


class CampaignFactory(DjangoModelFactory):
    class Meta:
        model = Campaign

    tenant = factory.LazyAttribute(lambda o: o.store.company.tenant)
    store = factory.SubFactory(StoreFactory)
    name = factory.Sequence(lambda n: f"Campaign {n}")
    segment = factory.SubFactory(
        CustomerSegmentFactory, tenant=factory.LazyAttribute(lambda o: o.factory_parent.tenant)
    )
    template = factory.SubFactory(
        CampaignTemplateFactory, tenant=factory.LazyAttribute(lambda o: o.factory_parent.tenant)
    )
    status = CampaignStatus.DRAFT


class CampaignRunFactory(DjangoModelFactory):
    class Meta:
        model = CampaignRun

    campaign = factory.SubFactory(CampaignFactory)
    status = CampaignStatus.RUNNING


class CampaignRecipientFactory(DjangoModelFactory):
    class Meta:
        model = CampaignRecipient

    run = factory.SubFactory(CampaignRunFactory)
    customer = factory.SubFactory(CustomerFactory)
    status = RecipientStatus.PENDING
    channel = "WHATSAPP"
    destination = factory.Sequence(lambda n: f"+5511{n:08d}")
