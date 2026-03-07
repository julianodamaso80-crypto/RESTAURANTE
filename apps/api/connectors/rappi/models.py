import uuid

from django.db import models
from django.utils import timezone


class RappiEnvironment(models.TextChoices):
    PROD = "prod", "Producao"
    DEV = "dev", "Desenvolvimento"


class RappiStoreCredential(models.Model):
    """Rappi credentials per store.

    Rappi uses a static token provided directly by the marketplace
    (no OAuth flow). The token is per-restaurant.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store = models.OneToOneField("tenants.Store", on_delete=models.CASCADE, related_name="rappi_credential")
    rappi_store_id = models.CharField(max_length=128, help_text="Store ID on Rappi platform")
    rappi_token = models.TextField(help_text="Bearer token provided by Rappi")
    webhook_secret = models.CharField(
        max_length=255, blank=True, default="", help_text="Secret for webhook validation"
    )
    environment = models.CharField(max_length=4, choices=RappiEnvironment.choices, default=RappiEnvironment.PROD)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Rappi Store Credential"

    def __str__(self):
        return f"Rappi Credential — Store {self.store_id} / Rappi Store {self.rappi_store_id}"

    @property
    def base_url(self) -> str:
        if self.environment == RappiEnvironment.DEV:
            return "https://microservices.dev.rappi.com/api/v2/restaurants-integrations-public-api"
        return "https://microservices.rappi.com.br/api/v2/restaurants-integrations-public-api"
