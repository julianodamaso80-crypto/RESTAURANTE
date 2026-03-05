"""99Food authentication via AppShopID.

The 99Food uses Open Delivery Protocol with client_credentials auth where:
  clientId     = AppShopID
  clientSecret = AppShopID (same value)

Reference: ERPs like Foody Delivery, Rcky, Cardapio Web use the same pattern.
"""

from datetime import timedelta

import requests
import structlog
from django.conf import settings
from django.utils import timezone

log = structlog.get_logger()

NINETYNINE_API_BASE = getattr(
    settings,
    "NINETYNINE_API_BASE_URL",
    "https://openapi.didi-food.com/v4/opendelivery",
)
NINETYNINE_AUTH_URL = f"{NINETYNINE_API_BASE}/authentication/v1.0/oauth/token"


class NinetyNineAuthError(Exception):
    pass


class NinetyNineAuthClient:
    """Authenticate with 99Food API via AppShopID."""

    def __init__(self, app_shop_id: str):
        self.app_shop_id = app_shop_id

    def get_token(self) -> dict:
        """Obtain access_token via client_credentials.

        Returns: {'access_token': ..., 'expires_in': ..., 'token_type': ...}
        """
        response = requests.post(
            NINETYNINE_AUTH_URL,
            data={
                "grantType": "client_credentials",
                "clientId": self.app_shop_id,
                "clientSecret": self.app_shop_id,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )

        if response.status_code != 200:
            log.error(
                "99food_auth_failed",
                status=response.status_code,
                body=response.text[:200],
            )
            raise NinetyNineAuthError(
                f"Autenticacao 99Food falhou: {response.status_code}. "
                f"Verifique se o AppShopID esta correto."
            )

        data = response.json()
        log.info("99food_auth_success", app_shop_id=self.app_shop_id[:4] + "***")
        return data

    def validate_credentials(self) -> dict:
        """Test if AppShopID is valid by fetching store data.

        Returns store data if valid, raises NinetyNineAuthError if invalid.
        """
        token_data = self.get_token()
        access_token = token_data.get("access_token", "")

        response = requests.get(
            f"{NINETYNINE_API_BASE}/merchant/v1/stores",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )

        if response.status_code == 401:
            raise NinetyNineAuthError(
                "AppShopID invalido. Verifique o codigo no painel do 99Food."
            )

        if response.status_code not in (200, 201):
            raise NinetyNineAuthError(
                f"Erro ao validar credenciais 99Food: {response.status_code}"
            )

        stores = response.json()
        log.info(
            "99food_credentials_valid",
            stores_count=len(stores) if isinstance(stores, list) else 1,
        )
        return {
            "token_data": token_data,
            "stores": stores if isinstance(stores, list) else [stores],
        }

    def save_credentials(self, store, token_data: dict, merchant_id: str = ""):
        """Save or update NinetyNineStoreCredential."""
        from connectors.ninetynine.models import NinetyNineStoreCredential

        expires_in = token_data.get("expires_in", 21600)

        cred, created = NinetyNineStoreCredential.objects.update_or_create(
            store=store,
            defaults={
                "merchant_id": merchant_id or self.app_shop_id,
                "client_id": self.app_shop_id,
                "client_secret": self.app_shop_id,
                "access_token": token_data.get("access_token", ""),
                "token_expires_at": timezone.now() + timedelta(seconds=expires_in),
                "is_active": True,
            },
        )

        action = "created" if created else "updated"
        log.info(
            "99food_credential_saved",
            store_id=str(store.id),
            merchant_id=merchant_id,
            action=action,
        )
        return cred
