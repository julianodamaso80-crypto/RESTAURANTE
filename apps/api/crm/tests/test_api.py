from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.django_db
def test_segment_list_requires_auth(api_client):
    response = api_client.get("/api/v1/crm/segments/")
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_create_segment(auth_client):
    response = auth_client.post(
        "/api/v1/crm/segments/",
        {"name": "Clientes VIP", "criteria": [{"criteria": "RFV_FREQUENCY_GTE", "value": 5}]},
        content_type="application/json",
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Clientes VIP"


@pytest.mark.django_db
def test_list_segments(auth_client, segment_factory):
    segment_factory()
    segment_factory()
    response = auth_client.get("/api/v1/crm/segments/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_segment_preview_endpoint(auth_client, segment_factory):
    segment = segment_factory()
    response = auth_client.get(f"/api/v1/crm/segments/{segment.id}/preview/")
    assert response.status_code == 200
    assert "total" in response.json()


@pytest.mark.django_db
def test_create_template(auth_client):
    response = auth_client.post(
        "/api/v1/crm/templates/",
        {
            "name": "Olá {{name}}",
            "channel": "WHATSAPP",
            "body": "Oi {{name}}, temos uma oferta especial pra você!",
        },
        content_type="application/json",
    )
    assert response.status_code == 201


@pytest.mark.django_db
def test_list_templates(auth_client, campaign_template_factory):
    campaign_template_factory()
    response = auth_client.get("/api/v1/crm/templates/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_create_campaign(auth_client, segment_factory, campaign_template_factory):
    segment = segment_factory()
    template = campaign_template_factory()
    response = auth_client.post(
        "/api/v1/crm/campaigns/",
        {
            "name": "Black Friday",
            "segment": str(segment.id),
            "template": str(template.id),
        },
        content_type="application/json",
    )
    assert response.status_code == 201
    assert response.json()["status"] == "DRAFT"


@pytest.mark.django_db
def test_launch_campaign(auth_client, campaign_factory):
    campaign = campaign_factory(status="DRAFT")
    with patch("crm.tasks.execute_campaign_run") as mock_task:
        mock_task.delay = MagicMock()
        response = auth_client.post(f"/api/v1/crm/campaigns/{campaign.id}/launch/")
    assert response.status_code == 201


@pytest.mark.django_db
def test_launch_scheduled_campaign(auth_client, campaign_factory):
    """Campanha SCHEDULED também pode ser lançada."""
    campaign = campaign_factory(status="SCHEDULED")
    with patch("crm.tasks.execute_campaign_run") as mock_task:
        mock_task.delay = MagicMock()
        response = auth_client.post(f"/api/v1/crm/campaigns/{campaign.id}/launch/")
    assert response.status_code == 201


@pytest.mark.django_db
def test_launch_completed_campaign_returns_400(auth_client, campaign_factory):
    campaign = campaign_factory(status="COMPLETED")
    response = auth_client.post(f"/api/v1/crm/campaigns/{campaign.id}/launch/")
    assert response.status_code == 400


@pytest.mark.django_db
def test_launch_running_campaign_returns_400(auth_client, campaign_factory):
    campaign = campaign_factory(status="RUNNING")
    response = auth_client.post(f"/api/v1/crm/campaigns/{campaign.id}/launch/")
    assert response.status_code == 400


@pytest.mark.django_db
def test_campaign_runs_endpoint(auth_client, campaign_factory):
    campaign = campaign_factory()
    response = auth_client.get(f"/api/v1/crm/campaigns/{campaign.id}/runs/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.django_db
def test_billing_quota_endpoint(auth_client):
    response = auth_client.get("/api/v1/crm/billing/quota/")
    assert response.status_code == 200
    data = response.json()
    assert "usage_pct" in data
    assert "is_blocked" in data
    assert "max_contacts" in data


@pytest.mark.django_db
def test_segment_scoped_to_tenant(auth_client, tenant_factory):
    """Segmentos de outro tenant não aparecem na listagem."""
    from crm.tests.factories import CustomerSegmentFactory

    other_tenant = tenant_factory()
    CustomerSegmentFactory(tenant=other_tenant, name="Other Tenant Segment")
    response = auth_client.get("/api/v1/crm/segments/")
    assert response.status_code == 200
    names = [s["name"] for s in response.json()]
    assert "Other Tenant Segment" not in names


@pytest.mark.django_db
def test_template_requires_auth(api_client):
    response = api_client.get("/api/v1/crm/templates/")
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_campaign_requires_auth(api_client):
    response = api_client.get("/api/v1/crm/campaigns/")
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_billing_requires_auth(api_client):
    response = api_client.get("/api/v1/crm/billing/quota/")
    assert response.status_code in (401, 403)
