from rest_framework.routers import DefaultRouter

from .views import (
    FranchiseeOnboardingViewSet,
    FranchiseTemplateViewSet,
    NetworkAlertViewSet,
    NetworkReportViewSet,
    StoreOverrideViewSet,
)

router = DefaultRouter()
router.register(r"enterprise/templates", FranchiseTemplateViewSet, basename="enterprise-template")
router.register(r"enterprise/overrides", StoreOverrideViewSet, basename="enterprise-override")
router.register(r"enterprise/onboardings", FranchiseeOnboardingViewSet, basename="enterprise-onboarding")
router.register(r"enterprise/reports", NetworkReportViewSet, basename="enterprise-report")
router.register(r"enterprise/alerts", NetworkAlertViewSet, basename="enterprise-alert")

urlpatterns = router.urls
