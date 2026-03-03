import factory
from factory.django import DjangoModelFactory

from kds.models import KDSStation, KDSStationCategory, KDSTicket, KDSTicketStatus
from orders.tests.factories import OrderFactory, StoreFactory


class KDSStationFactory(DjangoModelFactory):
    class Meta:
        model = KDSStation

    store = factory.SubFactory(StoreFactory)
    name = factory.Sequence(lambda n: f"Station {n}")
    category = KDSStationCategory.GENERAL
    is_active = True
    display_order = factory.Sequence(lambda n: n)


class KDSTicketFactory(DjangoModelFactory):
    class Meta:
        model = KDSTicket

    station = factory.SubFactory(KDSStationFactory)
    order = factory.SubFactory(OrderFactory)
    status = KDSTicketStatus.WAITING
