import factory
from factory.django import DjangoModelFactory

from catalog.models import (
    Catalog,
    CatalogStatus,
    Category,
    ChannelType,
    ModifierGroup,
    ModifierOption,
    Product,
    ProductAvailability,
    ProductChannelMap,
)
from orders.tests.factories import StoreFactory


class CatalogFactory(DjangoModelFactory):
    class Meta:
        model = Catalog

    store = factory.SubFactory(StoreFactory)
    company = factory.LazyAttribute(lambda o: o.store.company)
    tenant = factory.LazyAttribute(lambda o: o.store.company.tenant)
    name = factory.Sequence(lambda n: f"Cardápio {n}")
    status = CatalogStatus.ACTIVE


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    catalog = factory.SubFactory(CatalogFactory)
    name = factory.Sequence(lambda n: f"Categoria {n}")
    status = CatalogStatus.ACTIVE


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    category = factory.SubFactory(CategoryFactory)
    name = factory.Sequence(lambda n: f"Produto {n}")
    price_cents = 2000
    status = CatalogStatus.ACTIVE


class ModifierGroupFactory(DjangoModelFactory):
    class Meta:
        model = ModifierGroup

    product = factory.SubFactory(ProductFactory)
    name = factory.Sequence(lambda n: f"Grupo {n}")
    min_choices = 0
    max_choices = 1


class ModifierOptionFactory(DjangoModelFactory):
    class Meta:
        model = ModifierOption

    group = factory.SubFactory(ModifierGroupFactory)
    name = factory.Sequence(lambda n: f"Opção {n}")
    price_delta_cents = 0


class ProductChannelMapFactory(DjangoModelFactory):
    class Meta:
        model = ProductChannelMap

    product = factory.SubFactory(ProductFactory)
    channel = ChannelType.IFOOD
    external_id = factory.Sequence(lambda n: f"ext-{n}")


class ProductAvailabilityFactory(DjangoModelFactory):
    class Meta:
        model = ProductAvailability

    product = factory.SubFactory(ProductFactory)
    week_day = 0
    start_time = "08:00"
    end_time = "22:00"
