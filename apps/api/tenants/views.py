from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from audit.mixins import AuditMixin
from rbac.permissions import HasRBACPermission
from tenants.models import Company, Membership, Store, Tenant, User
from tenants.serializers import (
    CompanySerializer,
    MembershipSerializer,
    StoreSerializer,
    TenantSerializer,
    UserCreateSerializer,
    UserSerializer,
)


class TenantViewSet(AuditMixin, viewsets.ModelViewSet):
    """CRUD for tenants. Superuser only."""

    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    audit_entity_type = "tenant"


class CompanyViewSet(AuditMixin, viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    audit_entity_type = "company"
    rbac_permissions_map = {
        "list": "companies:read",
        "retrieve": "companies:read",
        "create": "companies:write",
        "update": "companies:write",
        "partial_update": "companies:write",
        "destroy": "companies:write",
    }

    def get_queryset(self):
        qs = Company.objects.select_related("tenant")
        tenant = getattr(self.request, "scope_tenant", None)
        if tenant:
            return qs.filter(tenant=tenant)
        if self.request.user.is_superuser:
            return qs.all()
        return qs.none()


class StoreViewSet(AuditMixin, viewsets.ModelViewSet):
    serializer_class = StoreSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    audit_entity_type = "store"
    rbac_permissions_map = {
        "list": "stores:read",
        "retrieve": "stores:read",
        "create": "stores:write",
        "update": "stores:write",
        "partial_update": "stores:write",
        "destroy": "stores:write",
    }

    def get_queryset(self):
        qs = Store.objects.select_related("company__tenant")
        store = getattr(self.request, "scope_store", None)
        company = getattr(self.request, "scope_company", None)
        tenant = getattr(self.request, "scope_tenant", None)
        if store:
            return qs.filter(id=store.id)
        if company:
            return qs.filter(company=company)
        if tenant:
            return qs.filter(company__tenant=tenant)
        if self.request.user.is_superuser:
            return qs.all()
        return qs.none()


class UserViewSet(AuditMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasRBACPermission]
    audit_entity_type = "user"
    rbac_permissions_map = {
        "list": "users:read",
        "retrieve": "users:read",
        "create": "users:write",
        "update": "users:write",
        "partial_update": "users:write",
        "destroy": "users:write",
    }

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        qs = User.objects.all()
        tenant = getattr(self.request, "scope_tenant", None)
        if tenant:
            return qs.filter(memberships__tenant=tenant).distinct()
        if self.request.user.is_superuser:
            return qs.all()
        return qs.none()


class MembershipViewSet(AuditMixin, viewsets.ModelViewSet):
    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    audit_entity_type = "membership"
    rbac_permissions_map = {
        "list": "memberships:read",
        "retrieve": "memberships:read",
        "create": "memberships:write",
        "update": "memberships:write",
        "partial_update": "memberships:write",
        "destroy": "memberships:write",
    }

    def get_queryset(self):
        qs = Membership.objects.select_related("user", "tenant", "company", "store")
        tenant = getattr(self.request, "scope_tenant", None)
        if tenant:
            return qs.filter(tenant=tenant)
        if self.request.user.is_superuser:
            return qs.all()
        return qs.none()
