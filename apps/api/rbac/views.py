from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from audit.mixins import AuditMixin
from rbac.models import Permission, Role, RoleBinding
from rbac.permissions import HasRBACPermission
from rbac.serializers import PermissionSerializer, RoleBindingSerializer, RoleSerializer


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """List all available permissions. Read-only."""

    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    rbac_permissions_map = {
        "list": "permissions:read",
        "retrieve": "permissions:read",
    }


class RoleViewSet(AuditMixin, viewsets.ModelViewSet):
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    audit_entity_type = "role"
    rbac_permissions_map = {
        "list": "roles:read",
        "retrieve": "roles:read",
        "create": "roles:write",
        "update": "roles:write",
        "partial_update": "roles:write",
        "destroy": "roles:write",
    }

    def get_queryset(self):
        qs = Role.objects.prefetch_related("permissions")
        tenant = getattr(self.request, "scope_tenant", None)
        if tenant:
            return qs.filter(tenant=tenant)
        if self.request.user.is_superuser:
            return qs.all()
        return qs.none()


class RoleBindingViewSet(AuditMixin, viewsets.ModelViewSet):
    serializer_class = RoleBindingSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    audit_entity_type = "rolebinding"
    rbac_permissions_map = {
        "list": "rolebindings:read",
        "retrieve": "rolebindings:read",
        "create": "rolebindings:write",
        "update": "rolebindings:write",
        "partial_update": "rolebindings:write",
        "destroy": "rolebindings:write",
    }

    def get_queryset(self):
        qs = RoleBinding.objects.select_related("user", "role", "tenant", "company", "store")
        tenant = getattr(self.request, "scope_tenant", None)
        if tenant:
            return qs.filter(tenant=tenant)
        if self.request.user.is_superuser:
            return qs.all()
        return qs.none()
