from django.urls import path

from .views import ifood_health, ifood_webhook

urlpatterns = [
    path("webhooks/ifood/", ifood_webhook, name="ifood-webhook"),
    path("health/ifood/", ifood_health, name="ifood-health"),
]
