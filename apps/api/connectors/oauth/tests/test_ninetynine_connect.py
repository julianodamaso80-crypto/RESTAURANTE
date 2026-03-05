import json
from unittest.mock import MagicMock, patch

import pytest

from connectors.ninetynine.models import NinetyNineStoreCredential


@pytest.mark.django_db
def test_connect_valid_app_shop_id(client, user_with_membership, store):
    client.force_login(user_with_membership)

    with patch("connectors.ninetynine.oauth.NinetyNineAuthClient") as MockClient:
        instance = MockClient.return_value
        instance.validate_credentials.return_value = {
            "token_data": {"access_token": "token-99", "expires_in": 21600},
            "stores": [{"id": "merchant-99-001", "name": "Restaurante Teste"}],
        }
        instance.save_credentials = MagicMock()

        with patch(
            "connectors.ninetynine.polling.start_polling_for_ninetynine_store"
        ) as mock_poll:
            mock_poll.delay = MagicMock()
            response = client.post(
                "/api/v1/connect/99food/connect/",
                data=json.dumps(
                    {
                        "store_id": str(store.id),
                        "app_shop_id": "APP-SHOP-12345",
                    }
                ),
                content_type="application/json",
            )

    assert response.status_code == 200
    data = response.json()
    assert data["connected"] is True
    assert data["provider"] == "99food"
    mock_poll.delay.assert_called_once_with(str(store.id))


@pytest.mark.django_db
def test_connect_invalid_app_shop_id_returns_400(client, user_with_membership, store):
    from connectors.ninetynine.oauth import NinetyNineAuthError

    client.force_login(user_with_membership)

    with patch("connectors.ninetynine.oauth.NinetyNineAuthClient") as MockClient:
        instance = MockClient.return_value
        instance.validate_credentials.side_effect = NinetyNineAuthError(
            "AppShopID invalido. Verifique o codigo no painel do 99Food."
        )

        response = client.post(
            "/api/v1/connect/99food/connect/",
            data=json.dumps(
                {
                    "store_id": str(store.id),
                    "app_shop_id": "INVALIDO",
                }
            ),
            content_type="application/json",
        )

    assert response.status_code == 400
    assert "AppShopID invalido" in response.json()["error"]


@pytest.mark.django_db
def test_connect_missing_app_shop_id_returns_400(client, user_with_membership, store):
    client.force_login(user_with_membership)

    response = client.post(
        "/api/v1/connect/99food/connect/",
        data=json.dumps({"store_id": str(store.id)}),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "AppShopID" in response.json()["error"]


@pytest.mark.django_db
def test_connect_missing_store_id_returns_400(client, user_with_membership):
    client.force_login(user_with_membership)

    response = client.post(
        "/api/v1/connect/99food/connect/",
        data=json.dumps({"app_shop_id": "APP-SHOP-12345"}),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "store_id" in response.json()["error"]


@pytest.mark.django_db
def test_connect_store_not_found_returns_404(client, user_with_membership):
    """User has no membership for a random store_id."""
    client.force_login(user_with_membership)

    response = client.post(
        "/api/v1/connect/99food/connect/",
        data=json.dumps(
            {
                "store_id": "00000000-0000-0000-0000-000000000000",
                "app_shop_id": "APP-SHOP-12345",
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_disconnect_deactivates_credential(client, user_with_membership, store):
    client.force_login(user_with_membership)

    NinetyNineStoreCredential.objects.create(
        store=store,
        merchant_id="merchant-99-001",
        client_id="APP-SHOP-12345",
        client_secret="APP-SHOP-12345",
        access_token="token-valid",
        is_active=True,
    )

    response = client.post(
        "/api/v1/connect/99food/disconnect/",
        data=json.dumps({"store_id": str(store.id)}),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json()["disconnected"] is True

    cred = NinetyNineStoreCredential.objects.get(store=store)
    assert cred.is_active is False
    assert cred.access_token == ""


@pytest.mark.django_db
def test_disconnect_nonexistent_returns_404(client, user_with_membership, store):
    client.force_login(user_with_membership)

    response = client.post(
        "/api/v1/connect/99food/disconnect/",
        data=json.dumps({"store_id": str(store.id)}),
        content_type="application/json",
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_status_shows_99food_connected(api_client, user_with_membership, store):
    from datetime import timedelta

    from django.utils import timezone

    api_client.force_authenticate(user=user_with_membership)

    NinetyNineStoreCredential.objects.create(
        store=store,
        merchant_id="merchant-99-001",
        client_id="APP-SHOP-12345",
        client_secret="APP-SHOP-12345",
        access_token="token-valid",
        is_active=True,
        token_expires_at=timezone.now() + timedelta(hours=5),
    )

    response = api_client.get(f"/api/v1/connect/status/?store_id={store.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["ninetynine"]["status"] == "connected"
    assert data["ninetynine"]["merchant_id"] == "merchant-99-001"


@pytest.mark.django_db
def test_status_shows_disconnected_when_no_credentials(api_client, user_with_membership, store):
    api_client.force_authenticate(user=user_with_membership)

    response = api_client.get(f"/api/v1/connect/status/?store_id={store.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["ninetynine"]["status"] == "disconnected"
    assert data["ifood"]["status"] == "disconnected"


@pytest.mark.django_db
def test_unauthenticated_user_returns_401(client, store):
    response = client.post(
        "/api/v1/connect/99food/connect/",
        data=json.dumps(
            {
                "store_id": str(store.id),
                "app_shop_id": "APP-SHOP-12345",
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 401
