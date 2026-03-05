"""iFood OAuth 2.0 client for Authorization Code flow (distributed model)."""

from urllib.parse import urlencode

import requests
import structlog
from django.conf import settings
from django.utils import timezone

log = structlog.get_logger()


class IFoodOAuthError(Exception):
    """Raised when an iFood OAuth operation fails."""


class IFoodOAuthClient:
    """Handles iFood OAuth 2.0 Authorization Code flow.

    - get_authorization_url: builds the URL to redirect the user to iFood
    - exchange_code_for_token: exchanges authorization code for tokens
    - refresh_access_token: refreshes expired access token
    - get_merchant_ids: discovers merchant IDs for the authenticated user
    - save_credentials: persists tokens to IFoodStoreCredential
    """

    TIMEOUT = 15

    def __init__(self):
        self.client_id = settings.IFOOD_CLIENT_ID
        self.client_secret = settings.IFOOD_CLIENT_SECRET
        self.redirect_uri = settings.IFOOD_REDIRECT_URI
        self.auth_base = settings.IFOOD_AUTH_BASE
        self.api_base = settings.IFOOD_API_BASE_URL

    def get_authorization_url(self, state: str) -> str:
        """Build the iFood OAuth authorize URL."""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
        }
        url = f"{self.auth_base}/authorize?{urlencode(params)}"
        log.info("ifood_oauth_authorization_url_built", state=state[:8])
        return url

    def exchange_code_for_token(self, code: str) -> dict:
        """Exchange authorization code for access + refresh tokens."""
        url = f"{self.auth_base}/token"
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
        }

        log.info("ifood_oauth_exchanging_code")
        try:
            resp = requests.post(url, data=payload, timeout=self.TIMEOUT)
            resp.raise_for_status()
            token_data = resp.json()
            log.info("ifood_oauth_code_exchanged")
            return token_data
        except requests.RequestException as exc:
            log.error("ifood_oauth_token_exchange_failed", error=str(exc))
            raise IFoodOAuthError(f"Token exchange failed: {exc}") from exc

    def refresh_access_token(self, refresh_token: str) -> dict:
        """Refresh an expired access token."""
        url = f"{self.auth_base}/token"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        log.info("ifood_oauth_refreshing_token")
        try:
            resp = requests.post(url, data=payload, timeout=self.TIMEOUT)
            resp.raise_for_status()
            token_data = resp.json()
            log.info("ifood_oauth_token_refreshed")
            return token_data
        except requests.RequestException as exc:
            log.error("ifood_oauth_token_refresh_failed", error=str(exc))
            raise IFoodOAuthError(f"Token refresh failed: {exc}") from exc

    def get_merchant_ids(self, access_token: str) -> list[str]:
        """Discover merchant IDs for the authenticated user."""
        url = f"{self.api_base}/merchant/v1.0/merchants"
        headers = {"Authorization": f"Bearer {access_token}"}

        log.info("ifood_oauth_fetching_merchants")
        try:
            resp = requests.get(url, headers=headers, timeout=self.TIMEOUT)
            resp.raise_for_status()
            merchants = resp.json()
            merchant_ids = [m["id"] for m in merchants]
            log.info("ifood_oauth_merchants_found", count=len(merchant_ids))
            return merchant_ids
        except requests.RequestException as exc:
            log.error("ifood_oauth_merchant_fetch_failed", error=str(exc))
            raise IFoodOAuthError(f"Merchant discovery failed: {exc}") from exc

    def save_credentials(self, store, token_data: dict, merchant_id: str):
        """Persist OAuth tokens to IFoodStoreCredential (update_or_create)."""
        from .models import IFoodStoreCredential

        expires_in = token_data.get("expires_in", 3600)
        token_expires_at = timezone.now() + timezone.timedelta(seconds=expires_in)

        cred, created = IFoodStoreCredential.objects.update_or_create(
            store=store,
            defaults={
                "merchant_id": merchant_id,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "access_token": token_data.get("access_token", ""),
                "refresh_token": token_data.get("refresh_token", ""),
                "token_expires_at": token_expires_at,
                "is_active": True,
            },
        )

        action = "created" if created else "updated"
        log.info(
            "ifood_oauth_credentials_saved",
            store_id=str(store.id),
            merchant_id=merchant_id,
            action=action,
        )
        return cred
