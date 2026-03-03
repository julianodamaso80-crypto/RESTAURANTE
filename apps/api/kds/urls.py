from rest_framework.routers import DefaultRouter

from .views import KDSStationViewSet, KDSTicketViewSet

router = DefaultRouter()
router.register(r"kds/stations", KDSStationViewSet, basename="kds-station")
router.register(r"kds/tickets", KDSTicketViewSet, basename="kds-ticket")

urlpatterns = router.urls
