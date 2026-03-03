from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.django_db
def test_customer_list_requires_auth(api_client):
    response = api_client.get("/api/v1/customers/")
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_create_customer(auth_client):
    response = auth_client.post(
        "/api/v1/customers/",
        {
            "name": "João Silva",
            "phone": "+5511999999999",
            "email": "joao@exemplo.com",
        },
        format="json",
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "João Silva"
    assert data["rfv_frequency"] == 0


@pytest.mark.django_db
def test_customer_scoped_to_tenant(auth_client, customer_factory, other_tenant):
    my_customer = customer_factory()
    other_customer = customer_factory(tenant=other_tenant)
    response = auth_client.get("/api/v1/customers/")
    assert response.status_code == 200
    ids = [c["id"] for c in response.json()]
    assert str(my_customer.id) in ids
    assert str(other_customer.id) not in ids


@pytest.mark.django_db
def test_customer_retrieve(auth_client, customer_factory):
    c = customer_factory()
    response = auth_client.get(f"/api/v1/customers/{c.id}/")
    assert response.status_code == 200
    assert response.json()["id"] == str(c.id)
    assert "consent_summary" in response.json()


@pytest.mark.django_db
def test_customer_update(auth_client, customer_factory):
    c = customer_factory(name="Antigo")
    response = auth_client.patch(
        f"/api/v1/customers/{c.id}/",
        {"name": "Novo"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Novo"


@pytest.mark.django_db
def test_grant_consent_via_api(auth_client, customer_factory):
    customer = customer_factory()
    response = auth_client.post(
        f"/api/v1/customers/{customer.id}/consent/",
        {"channel": "WHATSAPP", "action": "grant", "source": "checkout"},
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["status"] == "GRANTED"


@pytest.mark.django_db
def test_revoke_consent_via_api(auth_client, customer_factory):
    customer = customer_factory()
    response = auth_client.post(
        f"/api/v1/customers/{customer.id}/consent/",
        {"channel": "EMAIL", "action": "revoke"},
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["status"] == "REVOKED"


@pytest.mark.django_db
def test_consent_history_endpoint(auth_client, customer_factory, consent_record_factory):
    c = customer_factory()
    consent_record_factory(customer=c)
    consent_record_factory(customer=c)
    response = auth_client.get(f"/api/v1/customers/{c.id}/consents/")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.django_db
def test_customer_events_endpoint(auth_client, customer_factory, customer_event_factory):
    c = customer_factory()
    customer_event_factory(customer=c)
    response = auth_client.get(f"/api/v1/customers/{c.id}/events/")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.django_db
def test_trigger_rfv_endpoint(auth_client, customer_factory):
    customer = customer_factory()
    with patch("cdp.tasks.recalculate_customer_rfv") as mock_task:
        mock_task.delay = MagicMock()
        response = auth_client.post(f"/api/v1/customers/{customer.id}/trigger-rfv/")
    assert response.status_code == 200
    assert response.json()["queued"] is True


@pytest.mark.django_db
def test_customer_consent_summary_in_detail(auth_client, customer_factory):
    """consent_summary shows all channels with default False."""
    from cdp.consent import grant_consent
    from cdp.models import ConsentChannel

    c = customer_factory()
    grant_consent(c, ConsentChannel.WHATSAPP, source="test")

    response = auth_client.get(f"/api/v1/customers/{c.id}/")
    summary = response.json()["consent_summary"]
    assert summary["WHATSAPP"] is True
    assert summary["EMAIL"] is False
    assert summary["SMS"] is False
    assert summary["PUSH"] is False


@pytest.mark.django_db
def test_customer_no_delete(auth_client, customer_factory):
    """DELETE not allowed on customers."""
    c = customer_factory()
    response = auth_client.delete(f"/api/v1/customers/{c.id}/")
    assert response.status_code == 405
