import pytest
from django.test import Client

from tenants.models import User


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(email="admin@test.com", password="adminpass123")


@pytest.fixture
def admin_client(superuser):
    client = Client()
    client.force_login(superuser)
    return client


@pytest.mark.django_db
def test_admin_index_accessible(admin_client):
    response = admin_client.get("/admin/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_admin_site_header(admin_client):
    response = admin_client.get("/admin/")
    assert b"Restaurante ERP" in response.content


@pytest.mark.django_db
def test_tenant_admin_accessible(admin_client):
    response = admin_client.get("/admin/tenants/tenant/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_order_admin_accessible(admin_client):
    response = admin_client.get("/admin/orders/order/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_customer_admin_accessible(admin_client):
    response = admin_client.get("/admin/cdp/customer/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_stock_item_admin_accessible(admin_client):
    response = admin_client.get("/admin/stock/stockitem/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_campaign_admin_accessible(admin_client):
    response = admin_client.get("/admin/crm/campaign/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_kds_station_admin_accessible(admin_client):
    response = admin_client.get("/admin/kds/kdsstation/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_catalog_admin_accessible(admin_client):
    response = admin_client.get("/admin/catalog/catalog/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_audit_event_admin_accessible(admin_client):
    response = admin_client.get("/admin/audit/auditevent/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_raw_event_admin_no_add(admin_client):
    """RawEvent is append-only: add page should be blocked."""
    response = admin_client.get("/admin/ifood/rawevent/add/")
    assert response.status_code in (403, 302)


@pytest.mark.django_db
def test_stock_movement_admin_no_add(admin_client):
    """StockMovement is append-only: add page should be blocked."""
    response = admin_client.get("/admin/stock/stockmovement/add/")
    assert response.status_code in (403, 302)


@pytest.mark.django_db
def test_consent_record_admin_no_add(admin_client):
    """ConsentRecord is append-only: add page should be blocked."""
    response = admin_client.get("/admin/cdp/consentrecord/add/")
    assert response.status_code in (403, 302)


@pytest.mark.django_db
def test_audit_event_admin_no_add(admin_client):
    """AuditEvent is append-only: add page should be blocked."""
    response = admin_client.get("/admin/audit/auditevent/add/")
    assert response.status_code in (403, 302)


@pytest.mark.django_db
def test_idempotency_key_admin_no_add(admin_client):
    """IdempotencyKey is read-only: add page should be blocked."""
    response = admin_client.get("/admin/orders/idempotencykey/add/")
    assert response.status_code in (403, 302)
