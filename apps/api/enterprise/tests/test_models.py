import pytest
from django.db import IntegrityError


@pytest.mark.django_db
def test_franchise_template_creation(franchise_template_factory):
    t = franchise_template_factory()
    assert t.pk is not None
    assert t.is_active is True


@pytest.mark.django_db
def test_store_override_get_product_price(store_override_factory, product_factory):
    p = product_factory(price_cents=2890)
    override = store_override_factory(product_price_overrides={str(p.id): 3200})
    assert override.get_product_price(p) == 3200


@pytest.mark.django_db
def test_store_override_default_price(store_override_factory, product_factory):
    p = product_factory(price_cents=2890)
    override = store_override_factory(product_price_overrides={})
    assert override.get_product_price(p) == 2890


@pytest.mark.django_db
def test_store_override_product_inactive(store_override_factory, product_factory):
    p = product_factory(status="ACTIVE")
    override = store_override_factory(product_status_overrides={str(p.id): "INACTIVE"})
    assert override.is_product_active(p) is False


@pytest.mark.django_db
def test_store_override_product_default_active(store_override_factory, product_factory):
    p = product_factory(status="ACTIVE")
    override = store_override_factory(product_status_overrides={})
    assert override.is_product_active(p) is True


@pytest.mark.django_db
def test_onboarding_unique_per_template_store(franchisee_onboarding_factory, franchise_template_factory, store_factory):
    template = franchise_template_factory()
    store = store_factory()
    franchisee_onboarding_factory(template=template, store=store)
    with pytest.raises(IntegrityError):
        franchisee_onboarding_factory(template=template, store=store)


@pytest.mark.django_db
def test_network_report_str(network_report_factory):
    r = network_report_factory()
    assert "NetworkReport" in str(r)


@pytest.mark.django_db
def test_network_alert_str(network_alert_factory):
    a = network_alert_factory()
    assert "NetworkAlert" in str(a)
