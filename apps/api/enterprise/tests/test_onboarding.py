from unittest.mock import MagicMock, patch

import pytest

from enterprise.models import FranchiseeOnboarding, OnboardingStatus


@pytest.mark.django_db
def test_onboarding_runs_all_steps(franchise_template_factory, store_factory):
    from enterprise.onboarding import run_onboarding

    template = franchise_template_factory()
    store = store_factory(company=template.company)
    ob = FranchiseeOnboarding.objects.create(template=template, store=store)

    run_onboarding(str(ob.id))

    ob.refresh_from_db()
    assert ob.status == OnboardingStatus.DONE
    assert ob.completed_at is not None
    assert len(ob.steps_completed) == 5


@pytest.mark.django_db
def test_onboarding_is_idempotent(franchise_template_factory, store_factory):
    """Rodar onboarding duas vezes não duplica dados."""
    from enterprise.onboarding import run_onboarding
    from kds.models import KDSStation

    template = franchise_template_factory(
        default_kds_stations=[{"name": "Chapa", "category": "GRILL", "display_order": 1}]
    )
    store = store_factory(company=template.company)
    ob = FranchiseeOnboarding.objects.create(template=template, store=store)

    run_onboarding(str(ob.id))
    # Reset status to allow re-run
    ob.refresh_from_db()
    ob.status = OnboardingStatus.PENDING
    ob.save(update_fields=["status"])
    run_onboarding(str(ob.id))

    assert KDSStation.objects.filter(store=store, name="Chapa").count() == 1


@pytest.mark.django_db
def test_onboarding_copies_kds_stations(franchise_template_factory, store_factory):
    from enterprise.onboarding import run_onboarding
    from kds.models import KDSStation

    template = franchise_template_factory(
        default_kds_stations=[
            {"name": "Chapa", "category": "GRILL", "display_order": 1},
            {"name": "Bebidas", "category": "DRINKS", "display_order": 2},
        ]
    )
    store = store_factory(company=template.company)
    ob = FranchiseeOnboarding.objects.create(template=template, store=store)

    run_onboarding(str(ob.id))

    stations = KDSStation.objects.filter(store=store)
    assert stations.count() == 2
    assert stations.filter(name="Chapa").exists()


@pytest.mark.django_db
def test_onboarding_failed_status_on_error(franchise_template_factory, store_factory):
    from enterprise.onboarding import run_onboarding

    template = franchise_template_factory()
    store = store_factory(company=template.company)
    ob = FranchiseeOnboarding.objects.create(template=template, store=store)

    with patch("enterprise.onboarding._copy_catalog", side_effect=Exception("DB error")):
        with pytest.raises(Exception):
            run_onboarding(str(ob.id))

    ob.refresh_from_db()
    assert ob.status == OnboardingStatus.FAILED
    assert "DB error" in ob.error_detail


@pytest.mark.django_db
def test_onboarding_resumes_from_completed_steps(franchise_template_factory, store_factory):
    """Onboarding retomado após falha não reexecuta steps já concluídos."""
    from enterprise.onboarding import run_onboarding

    template = franchise_template_factory()
    store = store_factory(company=template.company)
    ob = FranchiseeOnboarding.objects.create(
        template=template,
        store=store,
        steps_completed=["copy_catalog", "copy_kds_stations"],
    )

    mock_catalog = MagicMock()
    with patch("enterprise.onboarding._copy_catalog", mock_catalog):
        run_onboarding(str(ob.id))

    mock_catalog.assert_not_called()


@pytest.mark.django_db
def test_onboarding_copies_catalog(
    franchise_template_factory, store_factory, catalog_factory, category_factory, product_factory
):
    """Onboarding copia catálogo com categorias e produtos."""
    from catalog.models import Catalog, Product
    from enterprise.onboarding import run_onboarding

    template = franchise_template_factory()
    catalog = catalog_factory(store=None, company=template.company, tenant=template.company.tenant)
    template.template_catalog = catalog
    template.save()

    cat = category_factory(catalog=catalog, name="Lanches")
    product_factory(category=cat, name="X-Burger", price_cents=2500)

    store = store_factory(company=template.company)
    ob = FranchiseeOnboarding.objects.create(template=template, store=store)

    run_onboarding(str(ob.id))

    store_catalog = Catalog.objects.get(store=store)
    assert store_catalog.name == catalog.name
    assert Product.objects.filter(category__catalog=store_catalog, name="X-Burger").exists()


@pytest.mark.django_db
def test_onboarding_not_found_returns_none(db):
    """run_onboarding com ID inexistente não levanta exceção."""
    from enterprise.onboarding import run_onboarding

    run_onboarding("00000000-0000-0000-0000-000000000000")
