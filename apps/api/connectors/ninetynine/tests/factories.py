import factory
from factory.django import DjangoModelFactory

from connectors.ifood.models import RawEvent, RawEventStatus
from connectors.ninetynine.models import NinetyNineStoreCredential
from orders.tests.factories import StoreFactory


class RawEventFactory(DjangoModelFactory):
    class Meta:
        model = RawEvent

    source = "99food"
    event_id = factory.Sequence(lambda n: f"evt-99-{n:06d}")
    event_type = "PLACED"
    payload = factory.LazyFunction(
        lambda: {"id": "evt-99-001", "merchantId": "merchant-99-001", "orderId": "order-99-001"}
    )
    headers = factory.LazyFunction(dict)
    status = RawEventStatus.RECEIVED


class NinetyNineStoreCredentialFactory(DjangoModelFactory):
    class Meta:
        model = NinetyNineStoreCredential

    store = factory.SubFactory(StoreFactory)
    merchant_id = factory.Sequence(lambda n: f"merchant-99-{n:04d}")
    client_id = factory.Sequence(lambda n: f"client-99-{n}")
    client_secret = "test-client-secret"
    webhook_secret = "test-webhook-secret"
    access_token = "fake-access-token-99"
    is_active = True
