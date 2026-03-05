import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("restaurante")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Explicitly include task modules that are NOT named tasks.py
app.conf.include = [
    "connectors.ifood.polling",
    "connectors.ninetynine.polling",
]
