import pytest


@pytest.mark.django_db
def test_tasks_registered():
    from config.celery import app

    assert "enterprise.tasks.run_franchisee_onboarding" in app.tasks
    assert "enterprise.tasks.generate_network_report_task" in app.tasks
    assert "enterprise.tasks.check_network_alerts_task" in app.tasks


@pytest.mark.django_db
def test_run_franchisee_onboarding_task(franchise_template_factory, store_factory):
    from enterprise.models import FranchiseeOnboarding, OnboardingStatus
    from enterprise.tasks import run_franchisee_onboarding

    template = franchise_template_factory()
    store = store_factory(company=template.company)
    ob = FranchiseeOnboarding.objects.create(template=template, store=store)

    run_franchisee_onboarding(str(ob.id))

    ob.refresh_from_db()
    assert ob.status == OnboardingStatus.DONE


@pytest.mark.django_db
def test_generate_network_report_task(company_factory):
    from enterprise.models import NetworkReport
    from enterprise.tasks import generate_network_report_task

    company = company_factory()

    generate_network_report_task(str(company.id), "DAILY", "2024-01-01", "2024-01-31")

    assert NetworkReport.objects.filter(company=company, period="DAILY").exists()


@pytest.mark.django_db
def test_check_network_alerts_task(company_factory):
    from enterprise.tasks import check_network_alerts_task

    company = company_factory()
    # Should not crash with no stores
    check_network_alerts_task(str(company.id))
