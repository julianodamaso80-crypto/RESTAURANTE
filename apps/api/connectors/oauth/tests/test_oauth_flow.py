"""Tests for iFood OAuth 2.0 Authorization Code flow."""

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from connectors.ifood.models import IFoodStoreCredential
from connectors.oauth.models import OAuthState
from orders.tests.factories import StoreFactory, UserFactory


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def store(db):
    return StoreFactory()


@pytest.fixture
def api_client(user, store):
    client = APIClient()
    client.force_authenticate(user=user)
    client.store = store
    return client


@pytest.fixture
def store_headers(store):
    return {"HTTP_X_STORE_ID": str(store.id)}


@pytest.fixture
def oauth_state(user, store):
    return OAuthState.objects.create(
        store=store,
        user=user,
        provider="ifood",
    )


@pytest.fixture
def ifood_credential(store):
    return IFoodStoreCredential.objects.create(
        store=store,
        merchant_id="merchant-123",
        client_id="client-id",
        client_secret="client-secret",
        access_token="access-token-abc",
        refresh_token="refresh-token-xyz",
        token_expires_at=timezone.now() + timedelta(hours=1),
        is_active=True,
    )


# ---------------------------------------------------------------------------
# IFoodOAuthStartView
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestIFoodOAuthStart:
    URL = "/api/v1/connect/ifood/start/"

    def test_start_returns_authorization_url(self, api_client, store_headers):
        resp = api_client.post(self.URL, **store_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "authorization_url" in data
        assert "authorize" in data["authorization_url"]
        assert "response_type=code" in data["authorization_url"]

        # Verify OAuthState was created
        state = OAuthState.objects.filter(store=api_client.store, provider="ifood").first()
        assert state is not None
        assert state.state in data["authorization_url"]

    def test_start_requires_auth(self):
        client = APIClient()
        resp = client.post(self.URL)
        assert resp.status_code == 401

    def test_start_requires_store_id(self, api_client):
        resp = api_client.post(self.URL)
        assert resp.status_code == 400
        assert "X-Store-Id" in resp.json()["error"]


# ---------------------------------------------------------------------------
# ifood_oauth_callback
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestIFoodOAuthCallback:
    URL = "/api/v1/connect/ifood/callback/"

    @patch("connectors.oauth.views.IFoodOAuthClient")
    def test_callback_success_saves_credential(self, MockClient, oauth_state, store):
        mock_client = MagicMock()
        MockClient.return_value = mock_client
        mock_client.exchange_code_for_token.return_value = {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "expires_in": 3600,
        }
        mock_client.get_merchant_ids.return_value = ["merchant-abc"]
        mock_client.save_credentials.return_value = None

        client = APIClient()
        resp = client.get(self.URL, {"code": "auth-code-123", "state": oauth_state.state})

        assert resp.status_code == 302
        assert "oauth=success" in resp.url
        assert "provider=ifood" in resp.url

        mock_client.exchange_code_for_token.assert_called_once_with("auth-code-123")
        mock_client.get_merchant_ids.assert_called_once_with("new-access-token")
        mock_client.save_credentials.assert_called_once_with(
            store,
            {
                "access_token": "new-access-token",
                "refresh_token": "new-refresh-token",
                "expires_in": 3600,
            },
            "merchant-abc",
        )

        # State should be marked as used
        oauth_state.refresh_from_db()
        assert oauth_state.used is True

    def test_callback_invalid_state_redirects_error(self, db):
        client = APIClient()
        resp = client.get(self.URL, {"code": "some-code", "state": "invalid-state"})
        assert resp.status_code == 302
        assert "oauth=error" in resp.url
        assert "invalid_state" in resp.url

    def test_callback_expired_state_redirects_error(self, oauth_state):
        oauth_state.expires_at = timezone.now() - timedelta(minutes=1)
        oauth_state.save(update_fields=["expires_at"])

        client = APIClient()
        resp = client.get(self.URL, {"code": "some-code", "state": oauth_state.state})
        assert resp.status_code == 302
        assert "oauth=error" in resp.url
        assert "expired" in resp.url

    def test_callback_already_used_state_redirects_error(self, oauth_state):
        oauth_state.used = True
        oauth_state.save(update_fields=["used"])

        client = APIClient()
        resp = client.get(self.URL, {"code": "some-code", "state": oauth_state.state})
        assert resp.status_code == 302
        assert "oauth=error" in resp.url
        assert "already_used" in resp.url

    def test_callback_missing_params_redirects_error(self, db):
        client = APIClient()
        resp = client.get(self.URL)
        assert resp.status_code == 302
        assert "oauth=error" in resp.url
        assert "missing_params" in resp.url

    def test_callback_provider_error_redirects(self, db):
        client = APIClient()
        resp = client.get(self.URL, {"error": "access_denied"})
        assert resp.status_code == 302
        assert "oauth=error" in resp.url
        assert "provider_denied" in resp.url

    @patch("connectors.oauth.views.IFoodOAuthClient")
    def test_callback_token_exchange_failure_redirects_error(self, MockClient, oauth_state):
        from connectors.ifood.oauth import IFoodOAuthError

        mock_client = MagicMock()
        MockClient.return_value = mock_client
        mock_client.exchange_code_for_token.side_effect = IFoodOAuthError("failed")

        client = APIClient()
        resp = client.get(self.URL, {"code": "auth-code", "state": oauth_state.state})
        assert resp.status_code == 302
        assert "token_exchange_failed" in resp.url

    @patch("connectors.oauth.views.IFoodOAuthClient")
    def test_callback_no_merchants_redirects_error(self, MockClient, oauth_state):
        mock_client = MagicMock()
        MockClient.return_value = mock_client
        mock_client.exchange_code_for_token.return_value = {
            "access_token": "token",
            "refresh_token": "refresh",
            "expires_in": 3600,
        }
        mock_client.get_merchant_ids.return_value = []

        client = APIClient()
        resp = client.get(self.URL, {"code": "auth-code", "state": oauth_state.state})
        assert resp.status_code == 302
        assert "no_merchants" in resp.url


# ---------------------------------------------------------------------------
# IFoodDisconnectView
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestIFoodDisconnect:
    URL = "/api/v1/connect/ifood/disconnect/"

    def test_disconnect_deactivates_credential(self, api_client, store_headers, ifood_credential):
        resp = api_client.post(self.URL, **store_headers)
        assert resp.status_code == 200
        assert "disconnected" in resp.json()["detail"]

        ifood_credential.refresh_from_db()
        assert ifood_credential.is_active is False

    def test_disconnect_no_active_connection(self, api_client, store_headers):
        resp = api_client.post(self.URL, **store_headers)
        assert resp.status_code == 404

    def test_disconnect_requires_auth(self):
        client = APIClient()
        resp = client.post(self.URL)
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# IntegrationStatusView
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestIntegrationStatus:
    URL = "/api/v1/connect/status/"

    def test_status_returns_connected(self, api_client, store_headers, ifood_credential):
        resp = api_client.get(self.URL, **store_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["ifood"]["status"] == "connected"
        assert data["ifood"]["merchant_id"] == "merchant-123"
        assert data["ninetynine"]["status"] == "disconnected"

    def test_status_returns_disconnected(self, api_client, store_headers):
        resp = api_client.get(self.URL, **store_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["ifood"]["status"] == "disconnected"
        assert data["ninetynine"]["status"] == "disconnected"

    def test_status_requires_auth(self):
        client = APIClient()
        resp = client.get(self.URL)
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# OAuthState model
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestOAuthStateModel:
    def test_is_valid_when_fresh(self, oauth_state):
        assert oauth_state.is_valid is True

    def test_is_expired_after_ttl(self, oauth_state):
        oauth_state.expires_at = timezone.now() - timedelta(seconds=1)
        assert oauth_state.is_expired is True
        assert oauth_state.is_valid is False

    def test_is_invalid_when_used(self, oauth_state):
        oauth_state.used = True
        assert oauth_state.is_valid is False

    def test_state_token_is_unique(self, user, store):
        s1 = OAuthState.objects.create(store=store, user=user, provider="ifood")
        s2 = OAuthState.objects.create(store=store, user=user, provider="ifood")
        assert s1.state != s2.state


# ---------------------------------------------------------------------------
# IFoodOAuthClient
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestIFoodOAuthClient:
    @patch("connectors.ifood.oauth.requests.post")
    def test_exchange_code_for_token(self, mock_post):
        from connectors.ifood.oauth import IFoodOAuthClient

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "access_token": "at-123",
            "refresh_token": "rt-456",
            "expires_in": 3600,
        }
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        client = IFoodOAuthClient()
        result = client.exchange_code_for_token("auth-code")

        assert result["access_token"] == "at-123"
        assert result["refresh_token"] == "rt-456"
        mock_post.assert_called_once()

    @patch("connectors.ifood.oauth.requests.post")
    def test_refresh_access_token(self, mock_post):
        from connectors.ifood.oauth import IFoodOAuthClient

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "access_token": "new-at",
            "refresh_token": "new-rt",
            "expires_in": 3600,
        }
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        client = IFoodOAuthClient()
        result = client.refresh_access_token("old-rt")

        assert result["access_token"] == "new-at"

    @patch("connectors.ifood.oauth.requests.get")
    def test_get_merchant_ids(self, mock_get):
        from connectors.ifood.oauth import IFoodOAuthClient

        mock_resp = MagicMock()
        mock_resp.json.return_value = [{"id": "m-1"}, {"id": "m-2"}]
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        client = IFoodOAuthClient()
        result = client.get_merchant_ids("access-token")

        assert result == ["m-1", "m-2"]

    def test_save_credentials_creates_new(self, store):
        from connectors.ifood.oauth import IFoodOAuthClient

        client = IFoodOAuthClient()
        token_data = {
            "access_token": "at-new",
            "refresh_token": "rt-new",
            "expires_in": 7200,
        }
        cred = client.save_credentials(store, token_data, "merchant-new")

        assert cred.merchant_id == "merchant-new"
        assert cred.access_token == "at-new"
        assert cred.refresh_token == "rt-new"
        assert cred.is_active is True

    def test_save_credentials_updates_existing(self, store, ifood_credential):
        from connectors.ifood.oauth import IFoodOAuthClient

        client = IFoodOAuthClient()
        token_data = {
            "access_token": "updated-at",
            "refresh_token": "updated-rt",
            "expires_in": 3600,
        }
        cred = client.save_credentials(store, token_data, "merchant-updated")

        assert cred.id == ifood_credential.id
        assert cred.access_token == "updated-at"
        assert cred.merchant_id == "merchant-updated"

    def test_get_authorization_url(self):
        from connectors.ifood.oauth import IFoodOAuthClient

        client = IFoodOAuthClient()
        url = client.get_authorization_url("test-state-123")

        assert "authorize" in url
        assert "response_type=code" in url
        assert "test-state-123" in url
