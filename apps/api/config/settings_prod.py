# cache-bust: 2026-03-03
"""Production settings for the Restaurant ERP API (Easypanel deploy)."""

import os
from pathlib import Path

from config.settings import *  # noqa: F401, F403

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
DEBUG = False
SECRET_KEY = os.environ["SECRET_KEY"]
ALLOWED_HOSTS = ["*"]
CORS_ALLOW_ALL_ORIGINS = True

# ---------------------------------------------------------------------------
# Database — Postgres via environment
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "restaurante"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

# ---------------------------------------------------------------------------
# Celery — Redis via environment
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://localhost:6379/2")

# ---------------------------------------------------------------------------
# Static files — Whitenoise
# ---------------------------------------------------------------------------
STATIC_ROOT = BASE_DIR / "staticfiles"

MIDDLEWARE.insert(  # noqa: F405
    MIDDLEWARE.index("django.middleware.common.CommonMiddleware"),  # noqa: F405
    "whitenoise.middleware.WhiteNoiseMiddleware",
)

# ---------------------------------------------------------------------------
# Celery Beat
# ---------------------------------------------------------------------------
INSTALLED_APPS += ["django_celery_beat"]  # noqa: F405

