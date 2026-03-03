"""Root URL configuration."""

from django.contrib import admin
from django.urls import include, path

from core.views import health_worker

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("health.urls")),
    path("api/v1/auth/", include("authentication.urls")),
    path("api/v1/", include("tenants.urls")),
    path("api/v1/", include("rbac.urls")),
    path("api/v1/", include("audit.urls")),
    path("api/v1/", include("orders.urls")),
    path("api/v1/health/worker/", health_worker, name="health-worker"),
    path("api/v1/", include("connectors.ifood.urls")),
    path("api/v1/", include("connectors.ninetynine.urls")),
    path("api/v1/", include("kds.urls")),
    path("api/v1/", include("catalog.urls")),
    path("api/v1/", include("cdp.urls")),
    path("api/v1/", include("crm.urls")),
    path("api/v1/", include("stock.urls")),
    path("api/v1/", include("enterprise.urls")),
]
