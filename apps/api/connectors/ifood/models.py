import uuid

from django.db import models
from django.utils import timezone


class RawEventStatus(models.TextChoices):
    RECEIVED = "RECEIVED", "Recebido"
    ENQUEUED = "ENQUEUED", "Enfileirado"
    PROCESSING = "PROCESSING", "Processando"
    PROCESSED = "PROCESSED", "Processado"
    DUPLICATE = "DUPLICATE", "Duplicado"
    FAILED = "FAILED", "Falhou"


class RawEvent(models.Model):
    """Immutable record of every event received from an external source.

    Persisted BEFORE responding 202. Never delete, never edit payload.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.CharField(max_length=32, default="ifood")
    event_id = models.CharField(max_length=255, help_text="Event ID in the source system")
    event_type = models.CharField(max_length=64, blank=True, default="")

    # Tenant/Store — nullable because the event arrives before linking to a store
    tenant_id = models.UUIDField(null=True, blank=True)
    store_id = models.UUIDField(null=True, blank=True)

    payload = models.JSONField(help_text="Raw payload, immutable")
    headers = models.JSONField(default=dict, help_text="Relevant headers (no auth)")

    status = models.CharField(max_length=20, choices=RawEventStatus.choices, default=RawEventStatus.RECEIVED)
    error_detail = models.TextField(blank=True, default="")
    retry_count = models.PositiveSmallIntegerField(default=0)

    received_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-received_at"]
        indexes = [
            models.Index(fields=["source", "event_id"]),
            models.Index(fields=["status", "received_at"]),
            models.Index(fields=["tenant_id", "store_id"]),
        ]

    def __str__(self):
        return f"RawEvent {self.source}:{self.event_id} [{self.status}]"


class IFoodStoreCredential(models.Model):
    """OAuth credentials for iFood per store.

    client_secret should be stored encrypted in production.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store = models.OneToOneField("tenants.Store", on_delete=models.CASCADE, related_name="ifood_credential")
    merchant_id = models.CharField(max_length=128, help_text="iFood merchantId")
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255, help_text="Store encrypted in production")
    webhook_secret = models.CharField(max_length=255, blank=True, default="", help_text="Secret for X-IFood-Signature")
    access_token = models.TextField(blank=True, default="")
    token_expires_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "iFood Store Credential"

    def __str__(self):
        return f"iFood Credential — Store {self.store_id} / Merchant {self.merchant_id}"
