import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

import connectors.oauth.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("tenants", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="OAuthState",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "state",
                    models.CharField(
                        default=connectors.oauth.models.generate_state_token, max_length=64, unique=True
                    ),
                ),
                ("provider", models.CharField(default="ifood", max_length=32)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("expires_at", models.DateTimeField(default=connectors.oauth.models.default_expires_at)),
                ("used", models.BooleanField(default=False)),
                (
                    "store",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="oauth_states",
                        to="tenants.store",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="oauth_states",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["state"], name="oauth_oauthst_state_idx"),
                    models.Index(fields=["provider", "store"], name="oauth_oauthst_prov_store_idx"),
                ],
            },
        ),
    ]
