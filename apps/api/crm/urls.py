from rest_framework.routers import DefaultRouter

from .views import (
    BillingQuotaViewSet,
    CampaignTemplateViewSet,
    CampaignViewSet,
    CustomerSegmentViewSet,
)

router = DefaultRouter()
router.register(r"crm/segments", CustomerSegmentViewSet, basename="crm-segment")
router.register(r"crm/templates", CampaignTemplateViewSet, basename="crm-template")
router.register(r"crm/campaigns", CampaignViewSet, basename="crm-campaign")
router.register(r"crm/billing", BillingQuotaViewSet, basename="crm-billing")

urlpatterns = router.urls
