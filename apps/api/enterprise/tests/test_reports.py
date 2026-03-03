from datetime import date

import pytest

from enterprise.models import NetworkAlert, NetworkAlertType
from enterprise.reports import check_network_alerts, generate_network_report


@pytest.mark.django_db
def test_generate_network_report_structure(company_factory):
    company = company_factory()
    report = generate_network_report(str(company.id), "DAILY", date(2024, 1, 1), date(2024, 1, 31))
    assert "company" in report
    assert "network_totals" in report
    assert "stores" in report
    assert "total_orders" in report["network_totals"]


@pytest.mark.django_db
def test_generate_network_report_nonexistent_company(db):
    report = generate_network_report(
        "00000000-0000-0000-0000-000000000000", "DAILY", date(2024, 1, 1), date(2024, 1, 31)
    )
    assert report == {}


@pytest.mark.django_db
def test_check_network_alerts_no_crash(company_factory):
    company = company_factory()
    result = check_network_alerts(str(company.id))
    assert result == 0


@pytest.mark.django_db
def test_check_network_alerts_nonexistent_company(db):
    result = check_network_alerts("00000000-0000-0000-0000-000000000000")
    assert result == 0


@pytest.mark.django_db
def test_network_alert_created_for_critical_stock(company_factory, store_factory, stock_alert_factory):
    company = company_factory()
    store = store_factory(company=company)
    for _ in range(3):
        stock_alert_factory(store=store, is_resolved=False)

    check_network_alerts(str(company.id))

    assert NetworkAlert.objects.filter(
        company=company,
        store=store,
        alert_type=NetworkAlertType.STOCK_CRITICAL,
    ).exists()


@pytest.mark.django_db
def test_network_alert_not_created_below_threshold(company_factory, store_factory, stock_alert_factory):
    company = company_factory()
    store = store_factory(company=company)
    for _ in range(2):
        stock_alert_factory(store=store, is_resolved=False)

    check_network_alerts(str(company.id))

    assert not NetworkAlert.objects.filter(
        company=company,
        store=store,
        alert_type=NetworkAlertType.STOCK_CRITICAL,
    ).exists()


@pytest.mark.django_db
def test_network_report_with_store(company_factory, store_factory):
    company = company_factory()
    store_factory(company=company)
    report = generate_network_report(str(company.id), "DAILY", date(2024, 1, 1), date(2024, 1, 31))
    assert report["network_totals"]["stores_count"] == 1
