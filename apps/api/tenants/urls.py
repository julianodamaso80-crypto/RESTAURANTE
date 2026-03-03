from rest_framework.routers import DefaultRouter

from tenants.views import CompanyViewSet, MembershipViewSet, StoreViewSet, TenantViewSet, UserViewSet

router = DefaultRouter()
router.register("tenants", TenantViewSet, basename="tenants")
router.register("companies", CompanyViewSet, basename="companies")
router.register("stores", StoreViewSet, basename="stores")
router.register("users", UserViewSet, basename="users")
router.register("memberships", MembershipViewSet, basename="memberships")

urlpatterns = router.urls
