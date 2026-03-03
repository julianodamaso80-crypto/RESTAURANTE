from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.django_db
def test_templates_requires_auth(api_client):
    assert api_client.get("/api/v1/enterprise/templates/").status_code in (401, 403)


@pytest.mark.django_db
def test_create_franchise_template(auth_client):
    response = auth_client.post(
        "/api/v1/enterprise/templates/",
        {
            "name": "Template Padrão",
            "default_kds_stations": [{"name": "Chapa", "category": "GRILL", "display_order": 1}],
        },
        content_type="application/json",
    )
    assert response.status_code == 201


@pytest.mark.django_db
def test_list_franchise_templates(auth_client, franchise_template_factory):
    franchise_template_factory()
    response = auth_client.get("/api/v1/enterprise/templates/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_onboard_store_endpoint(auth_client, franchise_template_factory, store_factory):
    template = franchise_template_factory()
    store = store_factory(company=template.company)

    with patch("enterprise.tasks.run_franchisee_onboarding") as mock_task:
        mock_task.delay = MagicMock()
        response = auth_client.post(
            f"/api/v1/enterprise/templates/{template.id}/onboard-store/",
            {"store_id": str(store.id)},
            content_type="application/json",
        )
    assert response.status_code == 202


@pytest.mark.django_db
def test_onboard_store_missing_store_id(auth_client, franchise_template_factory):
    template = franchise_template_factory()
    response = auth_client.post(
        f"/api/v1/enterprise/templates/{template.id}/onboard-store/",
        {},
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_onboard_store_not_found(auth_client, franchise_template_factory):
    template = franchise_template_factory()
    response = auth_client.post(
        f"/api/v1/enterprise/templates/{template.id}/onboard-store/",
        {"store_id": "00000000-0000-0000-0000-000000000000"},
        content_type="application/json",
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_network_report_generate(auth_client):
    with patch("enterprise.tasks.generate_network_report_task") as mock_task:
        mock_task.delay = MagicMock()
        response = auth_client.post(
            "/api/v1/enterprise/reports/generate/",
            {
                "period": "DAILY",
                "date_from": "2024-01-01",
                "date_to": "2024-01-31",
            },
            content_type="application/json",
        )
    assert response.status_code == 202
    assert response.json()["queued"] is True


@pytest.mark.django_db
def test_network_report_generate_missing_dates(auth_client):
    response = auth_client.post(
        "/api/v1/enterprise/reports/generate/",
        {"period": "DAILY"},
        content_type="application/json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_network_alerts_open_by_default(auth_client, network_alert_factory):
    open_alert = network_alert_factory(is_resolved=False)
    network_alert_factory(is_resolved=True)
    response = auth_client.get("/api/v1/enterprise/alerts/")
    assert response.status_code == 200
    data = response.json()
    # Handle both paginated and non-paginated responses
    results = data.get("results", data) if isinstance(data, dict) else data
    ids = [a["id"] for a in results]
    assert str(open_alert.id) in ids


@pytest.mark.django_db
def test_resolve_network_alert(auth_client, network_alert_factory):
    alert = network_alert_factory(is_resolved=False)
    response = auth_client.post(f"/api/v1/enterprise/alerts/{alert.id}/resolve/")
    assert response.status_code == 200
    assert response.json()["is_resolved"] is True


@pytest.mark.django_db
def test_check_alerts_endpoint(auth_client):
    with patch("enterprise.tasks.check_network_alerts_task") as mock_task:
        mock_task.delay = MagicMock()
        response = auth_client.post("/api/v1/enterprise/alerts/check/")
    assert response.status_code == 200
    assert response.json()["queued"] is True


@pytest.mark.django_db
def test_retry_onboarding_failed(auth_client, franchise_template_factory, store_factory):
    from enterprise.models import FranchiseeOnboarding, OnboardingStatus

    template = franchise_template_factory()
    store = store_factory(company=template.company)
    ob = FranchiseeOnboarding.objects.create(
        template=template, store=store, status=OnboardingStatus.FAILED, error_detail="some error"
    )

    with patch("enterprise.tasks.run_franchisee_onboarding") as mock_task:
        mock_task.delay = MagicMock()
        response = auth_client.post(f"/api/v1/enterprise/onboardings/{ob.id}/retry/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_retry_onboarding_not_failed(auth_client, franchise_template_factory, store_factory):
    from enterprise.models import FranchiseeOnboarding, OnboardingStatus

    template = franchise_template_factory()
    store = store_factory(company=template.company)
    ob = FranchiseeOnboarding.objects.create(template=template, store=store, status=OnboardingStatus.DONE)

    response = auth_client.post(f"/api/v1/enterprise/onboardings/{ob.id}/retry/")
    assert response.status_code == 400
