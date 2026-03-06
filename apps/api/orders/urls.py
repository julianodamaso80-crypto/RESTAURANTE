from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import OrderViewSet, PublicOrderCreateView, PublicOrderDetailView

router = DefaultRouter()
router.register(r"orders", OrderViewSet, basename="order")

urlpatterns = [
    path("orders/public/", PublicOrderCreateView.as_view(), name="public-order-create"),
    path("orders/public/<uuid:pk>/", PublicOrderDetailView.as_view(), name="public-order-detail"),
] + router.urls
