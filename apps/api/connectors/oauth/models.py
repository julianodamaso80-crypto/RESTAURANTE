import secrets
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


def generate_state_token():
    return secrets.token_urlsafe(32)


def default_expires_at():
    return timezone.now() + timezone.timedelta(minutes=10)


class OAuthState(models.Model):
    """Anti-CSRF token for OAuth Authorization Code flow.

    Created when a user starts the OAuth flow, validated on callback.
    Expires after 10 minutes. Single-use (marked used=True after callback).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    state = models.CharField(max_length=64, unique=True, default=generate_state_token)
    store = models.ForeignKey("tenants.Store", on_delete=models.CASCADE, related_name="oauth_states")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="oauth_states")
    provider = models.CharField(max_length=32, default="ifood")

    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(default=default_expires_at)
    used = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["state"]),
            models.Index(fields=["provider", "store"]),
        ]

    def __str__(self):
        return f"OAuthState {self.provider} — Store {self.store_id} [{self.state[:8]}...]"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.used and not self.is_expired
