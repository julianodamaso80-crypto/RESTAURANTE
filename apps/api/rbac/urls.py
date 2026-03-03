from rest_framework.routers import DefaultRouter

from rbac.views import PermissionViewSet, RoleBindingViewSet, RoleViewSet

router = DefaultRouter()
router.register("permissions", PermissionViewSet, basename="permissions")
router.register("roles", RoleViewSet, basename="roles")
router.register("role-bindings", RoleBindingViewSet, basename="role-bindings")

urlpatterns = router.urls
