from rest_framework.routers import DefaultRouter

from .views import BillOfMaterialsViewSet, StockAlertViewSet, StockItemViewSet, StockMovementViewSet

router = DefaultRouter()
router.register(r"stock/items", StockItemViewSet, basename="stock-item")
router.register(r"stock/movements", StockMovementViewSet, basename="stock-movement")
router.register(r"stock/alerts", StockAlertViewSet, basename="stock-alert")
router.register(r"stock/bom", BillOfMaterialsViewSet, basename="stock-bom")

urlpatterns = router.urls
