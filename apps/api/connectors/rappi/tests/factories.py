import factory
from factory.django import DjangoModelFactory

from connectors.ifood.models import RawEvent, RawEventStatus
from connectors.rappi.models import RappiStoreCredential
from orders.tests.factories import StoreFactory


class RappiRawEventFactory(DjangoModelFactory):
    class Meta:
        model = RawEvent

    source = "rappi"
    event_id = factory.Sequence(lambda n: f"evt-rappi-{n:06d}")
    event_type = "NEW_ORDER"
    payload = factory.LazyFunction(
        lambda: {"id": "evt-rappi-001", "store_id": "rappi-store-001", "orderId": "order-rappi-001"}
    )
    headers = factory.LazyFunction(dict)
    status = RawEventStatus.RECEIVED


class RappiStoreCredentialFactory(DjangoModelFactory):
    class Meta:
        model = RappiStoreCredential

    store = factory.SubFactory(StoreFactory)
    rappi_store_id = factory.Sequence(lambda n: f"rappi-store-{n:04d}")
    rappi_token = "fake-rappi-token"
    webhook_secret = "test-rappi-secret"
    environment = "prod"
    is_active = True
