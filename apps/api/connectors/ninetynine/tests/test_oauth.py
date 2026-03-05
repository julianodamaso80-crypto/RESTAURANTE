from unittest.mock import MagicMock, patch

import pytest

from connectors.ninetynine.models import NinetyNineStoreCredential
from connectors.ninetynine.oauth import NinetyNineAuthClient, NinetyNineAuthError


class TestNinetyNineAuthClientGetToken:
    def test_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "tok-123",
            "expires_in": 21600,
            "token_type": "Bearer",
        }

        client = NinetyNineAuthClient(app_shop_id="APP-SHOP-001")

        with patch("connectors.ninetynine.oauth.requests.post", return_value=mock_response) as mock_post:
            result = client.get_token()

        assert result["access_token"] == "tok-123"
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["data"]["clientId"] == "APP-SHOP-001"
        assert call_kwargs[1]["data"]["clientSecret"] == "APP-SHOP-001"

    def test_failure_raises_auth_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        client = NinetyNineAuthClient(app_shop_id="INVALID")

        with patch("connectors.ninetynine.oauth.requests.post", return_value=mock_response):
            with pytest.raises(NinetyNineAuthError, match="Autenticacao 99Food falhou"):
                client.get_token()


class TestNinetyNineAuthClientValidateCredentials:
    def test_valid_credentials(self):
        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {
            "access_token": "tok-valid",
            "expires_in": 21600,
        }

        mock_stores_response = MagicMock()
        mock_stores_response.status_code = 200
        mock_stores_response.json.return_value = [
            {"id": "store-001", "name": "Test Store"}
        ]

        client = NinetyNineAuthClient(app_shop_id="APP-SHOP-001")

        with patch("connectors.ninetynine.oauth.requests.post", return_value=mock_token_response):
            with patch("connectors.ninetynine.oauth.requests.get", return_value=mock_stores_response):
                result = client.validate_credentials()

        assert result["token_data"]["access_token"] == "tok-valid"
        assert len(result["stores"]) == 1
        assert result["stores"][0]["id"] == "store-001"

    def test_invalid_token_raises(self):
        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {"access_token": "tok-bad"}

        mock_stores_response = MagicMock()
        mock_stores_response.status_code = 401

        client = NinetyNineAuthClient(app_shop_id="APP-SHOP-BAD")

        with patch("connectors.ninetynine.oauth.requests.post", return_value=mock_token_response):
            with patch("connectors.ninetynine.oauth.requests.get", return_value=mock_stores_response):
                with pytest.raises(NinetyNineAuthError, match="AppShopID invalido"):
                    client.validate_credentials()

    def test_server_error_raises(self):
        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {"access_token": "tok-ok"}

        mock_stores_response = MagicMock()
        mock_stores_response.status_code = 500

        client = NinetyNineAuthClient(app_shop_id="APP-SHOP-001")

        with patch("connectors.ninetynine.oauth.requests.post", return_value=mock_token_response):
            with patch("connectors.ninetynine.oauth.requests.get", return_value=mock_stores_response):
                with pytest.raises(NinetyNineAuthError, match="Erro ao validar"):
                    client.validate_credentials()


class TestNinetyNineAuthClientSaveCredentials:
    @pytest.mark.django_db
    def test_creates_new_credential(self, store_factory):
        from orders.tests.factories import StoreFactory

        store = StoreFactory()

        client = NinetyNineAuthClient(app_shop_id="APP-SHOP-001")
        token_data = {"access_token": "tok-new", "expires_in": 21600}

        cred = client.save_credentials(store, token_data, merchant_id="merch-001")

        assert cred.store == store
        assert cred.client_id == "APP-SHOP-001"
        assert cred.client_secret == "APP-SHOP-001"
        assert cred.access_token == "tok-new"
        assert cred.merchant_id == "merch-001"
        assert cred.is_active is True

    @pytest.mark.django_db
    def test_updates_existing_credential(self, store_factory):
        from orders.tests.factories import StoreFactory

        store = StoreFactory()
        NinetyNineStoreCredential.objects.create(
            store=store,
            merchant_id="old-merch",
            client_id="OLD-APP",
            client_secret="OLD-APP",
            access_token="old-token",
            is_active=False,
        )

        client = NinetyNineAuthClient(app_shop_id="NEW-APP")
        token_data = {"access_token": "new-token", "expires_in": 21600}

        cred = client.save_credentials(store, token_data, merchant_id="new-merch")

        assert NinetyNineStoreCredential.objects.filter(store=store).count() == 1
        assert cred.client_id == "NEW-APP"
        assert cred.access_token == "new-token"
        assert cred.is_active is True
