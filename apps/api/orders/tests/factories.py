import factory
from factory.django import DjangoModelFactory

from orders.enums import OrderChannel, OrderType
from orders.models import Order, OrderItem
from tenants.models import Company, Store, Tenant, User


class TenantFactory(DjangoModelFactory):
    class Meta:
        model = Tenant

    name = factory.Sequence(lambda n: f"Tenant {n}")
    slug = factory.Sequence(lambda n: f"tenant-{n}")


class CompanyFactory(DjangoModelFactory):
    class Meta:
        model = Company

    tenant = factory.SubFactory(TenantFactory)
    name = factory.Sequence(lambda n: f"Company {n}")
    slug = factory.Sequence(lambda n: f"company-{n}")


class StoreFactory(DjangoModelFactory):
    class Meta:
        model = Store

    company = factory.SubFactory(CompanyFactory)
    name = factory.Sequence(lambda n: f"Store {n}")
    slug = factory.Sequence(lambda n: f"store-{n}")


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    name = factory.Sequence(lambda n: f"User {n}")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")


class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order

    tenant = factory.LazyAttribute(lambda o: o.store.company.tenant)
    store = factory.SubFactory(StoreFactory)
    display_number = factory.Sequence(lambda n: f"#{n:04d}")
    channel = OrderChannel.OWN
    order_type = OrderType.DELIVERY
    subtotal_cents = 2000
    total_cents = 2000


class OrderItemFactory(DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    name = factory.Faker("word")
    quantity = 1
    unit_price_cents = 2000
    total_cents = 2000
