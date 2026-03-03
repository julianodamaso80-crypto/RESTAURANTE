import factory
from factory.django import DjangoModelFactory

from enterprise.models import (
    FranchiseeOnboarding,
    FranchiseTemplate,
    NetworkAlert,
    NetworkAlertType,
    NetworkReport,
    OnboardingStatus,
    ReportPeriod,
    StoreOverride,
)
from orders.tests.factories import CompanyFactory, StoreFactory


class FranchiseTemplateFactory(DjangoModelFactory):
    class Meta:
        model = FranchiseTemplate

    company = factory.SubFactory(CompanyFactory)
    name = factory.Sequence(lambda n: f"Template {n}")
    default_kds_stations = factory.LazyFunction(list)
    is_active = True


class StoreOverrideFactory(DjangoModelFactory):
    class Meta:
        model = StoreOverride

    store = factory.SubFactory(StoreFactory)
    template = factory.SubFactory(FranchiseTemplateFactory)
    product_price_overrides = factory.LazyFunction(dict)
    product_status_overrides = factory.LazyFunction(dict)
    bom_overrides = factory.LazyFunction(dict)


class FranchiseeOnboardingFactory(DjangoModelFactory):
    class Meta:
        model = FranchiseeOnboarding

    template = factory.SubFactory(FranchiseTemplateFactory)
    store = factory.SubFactory(StoreFactory)
    status = OnboardingStatus.PENDING


class NetworkReportFactory(DjangoModelFactory):
    class Meta:
        model = NetworkReport

    company = factory.SubFactory(CompanyFactory)
    period = ReportPeriod.DAILY
    date_from = factory.LazyFunction(lambda: __import__("datetime").date(2024, 1, 1))
    date_to = factory.LazyFunction(lambda: __import__("datetime").date(2024, 1, 31))
    data = factory.LazyFunction(dict)


class NetworkAlertFactory(DjangoModelFactory):
    class Meta:
        model = NetworkAlert

    company = factory.LazyAttribute(lambda o: o.store.company)
    store = factory.SubFactory(StoreFactory)
    alert_type = NetworkAlertType.STOCK_CRITICAL
    payload = factory.LazyFunction(dict)
    is_resolved = False
