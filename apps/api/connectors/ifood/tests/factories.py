import factory
from factory.django import DjangoModelFactory

from connectors.ifood.models import IFoodStoreCredential, RawEvent, RawEventStatus
from orders.tests.factories import StoreFactory


class RawEventFactory(DjangoModelFactory):
    class Meta:
        model = RawEvent

    source = "ifood"
    event_id = factory.Sequence(lambda n: f"evt-{n:06d}")
    event_type = "PLACED"
    payload = factory.LazyFunction(lambda: {"id": "evt-001", "merchantId": "merchant-001", "orderId": "order-001"})
    headers = factory.LazyFunction(dict)
    status = RawEventStatus.RECEIVED


class IFoodStoreCredentialFactory(DjangoModelFactory):
    class Meta:
        model = IFoodStoreCredential

    store = factory.SubFactory(StoreFactory)
    merchant_id = factory.Sequence(lambda n: f"merchant-{n:04d}")
    client_id = factory.Sequence(lambda n: f"client-{n}")
    client_secret = "test-client-secret"
    webhook_secret = "test-webhook-secret"
    access_token = "fake-access-token"
    is_active = True
