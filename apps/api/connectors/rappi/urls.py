from django.urls import path

from .views import rappi_configure, rappi_disconnect, rappi_health, rappi_status, rappi_webhook

urlpatterns = [
    path("connect/rappi/webhook/", rappi_webhook, name="rappi-webhook"),
    path("health/rappi/", rappi_health, name="rappi-health"),
    path("connect/rappi/configure/", rappi_configure, name="rappi-configure"),
    path("connect/rappi/status/", rappi_status, name="rappi-status"),
    path("connect/rappi/disconnect/", rappi_disconnect, name="rappi-disconnect"),
]
