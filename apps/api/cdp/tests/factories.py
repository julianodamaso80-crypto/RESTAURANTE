import factory
from factory.django import DjangoModelFactory

from cdp.models import (
    ConsentChannel,
    ConsentRecord,
    ConsentStatus,
    Customer,
    CustomerEvent,
    CustomerEventType,
    CustomerIdentity,
    IdentityType,
)
from orders.tests.factories import TenantFactory


class CustomerFactory(DjangoModelFactory):
    class Meta:
        model = Customer

    tenant = factory.SubFactory(TenantFactory)
    name = factory.Faker("name")
    phone = factory.Sequence(lambda n: f"+5511{n:08d}")
    email = factory.Faker("email")


class CustomerIdentityFactory(DjangoModelFactory):
    class Meta:
        model = CustomerIdentity

    customer = factory.SubFactory(CustomerFactory)
    type = IdentityType.PHONE
    value = factory.Sequence(lambda n: f"+5511{n:08d}")


class ConsentRecordFactory(DjangoModelFactory):
    class Meta:
        model = ConsentRecord

    customer = factory.SubFactory(CustomerFactory)
    channel = ConsentChannel.WHATSAPP
    status = ConsentStatus.GRANTED


class CustomerEventFactory(DjangoModelFactory):
    class Meta:
        model = CustomerEvent

    customer = factory.SubFactory(CustomerFactory)
    event_type = CustomerEventType.ORDER_DELIVERED
    payload = factory.LazyFunction(dict)
