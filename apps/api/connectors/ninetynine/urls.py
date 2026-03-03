from django.urls import path

from .views import ninetynine_health, ninetynine_webhook

urlpatterns = [
    path("webhooks/99food/", ninetynine_webhook, name="99food-webhook"),
    path("health/99food/", ninetynine_health, name="99food-health"),
]
