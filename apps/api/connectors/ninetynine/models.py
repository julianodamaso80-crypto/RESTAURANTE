import uuid

from django.db import models
from django.utils import timezone


class NinetyNineStoreCredential(models.Model):
    """OAuth credentials for 99Food per store.

    99Food uses OAuth 2.0 Client Credentials (same pattern as iFood).
    client_secret should be stored encrypted in production.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store = models.OneToOneField("tenants.Store", on_delete=models.CASCADE, related_name="ninetynine_credential")
    merchant_id = models.CharField(max_length=128, help_text="merchantId 99Food")
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255, help_text="Store encrypted in production")
    webhook_secret = models.CharField(
        max_length=255, blank=True, default="", help_text="Secret for X-Ninetynine-Signature"
    )
    access_token = models.TextField(blank=True, default="")
    token_expires_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "99Food Store Credential"

    def __str__(self):
        return f"99Food Credential — Store {self.store_id} / Merchant {self.merchant_id}"
