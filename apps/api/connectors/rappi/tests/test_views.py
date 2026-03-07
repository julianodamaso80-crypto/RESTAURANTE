import pytest
from rest_framework.test import APIClient

from connectors.rappi.models import RappiStoreCredential
from orders.tests.factories import StoreFactory, UserFactory


@pytest.mark.django_db
def test_configure_creates_credential():
    from unittest.mock import patch

    user = UserFactory()
    store = StoreFactory()

    api_client = APIClient()
    api_client.force_authenticate(user=user)

    with patch("connectors.rappi.client.RappiAPIClient") as MockClient:
        MockClient.return_value.check_connection.return_value = True
        response = api_client.post(
            "/api/v1/connect/rappi/configure/",
            {"store_id": str(store.id), "rappi_token": "my-token", "rappi_store_id": "RS-001"},
            format="json",
        )

    assert response.status_code == 201
    assert response.data["status"] == "connected"
    assert RappiStoreCredential.objects.filter(store=store).exists()


@pytest.mark.django_db
def test_configure_requires_all_fields():
    user = UserFactory()
    api_client = APIClient()
    api_client.force_authenticate(user=user)

    response = api_client.post(
        "/api/v1/connect/rappi/configure/",
        {"store_id": "some-id"},
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_status_not_configured():
    user = UserFactory()
    store = StoreFactory()
    api_client = APIClient()
    api_client.force_authenticate(user=user)

    response = api_client.get(f"/api/v1/connect/rappi/status/?store_id={store.id}")
    assert response.status_code == 200
    assert response.data["status"] == "not_configured"


@pytest.mark.django_db
def test_disconnect_removes_credential():
    from .factories import RappiStoreCredentialFactory

    user = UserFactory()
    cred = RappiStoreCredentialFactory()
    store = cred.store

    api_client = APIClient()
    api_client.force_authenticate(user=user)

    response = api_client.delete(
        "/api/v1/connect/rappi/disconnect/",
        {"store_id": str(store.id)},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["status"] == "disconnected"
    assert not RappiStoreCredential.objects.filter(store=store).exists()
