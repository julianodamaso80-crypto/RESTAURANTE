from rest_framework.routers import DefaultRouter

from audit.views import AuditEventViewSet

router = DefaultRouter()
router.register("audit", AuditEventViewSet, basename="audit")

urlpatterns = router.urls
