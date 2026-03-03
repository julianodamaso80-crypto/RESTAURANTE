from django.db.models import Q
from rest_framework.permissions import BasePermission

from rbac.models import RoleBinding


def check_rbac_permission(user, permission_codename, tenant=None, company=None, store=None):
    """Check if user has a permission within the given scope.

    Scope hierarchy: store -> company -> tenant.
    A binding at tenant level grants access to all its companies and stores.
    A binding at company level grants access to all its stores.
    """
    bindings = RoleBinding.objects.filter(user=user)

    if store:
        scope_q = (
            Q(store=store)
            | Q(company=store.company, store__isnull=True)
            | Q(tenant=store.company.tenant, company__isnull=True, store__isnull=True)
        )
    elif company:
        scope_q = Q(company=company, store__isnull=True) | Q(
            tenant=company.tenant, company__isnull=True, store__isnull=True
        )
    elif tenant:
        scope_q = Q(tenant=tenant, company__isnull=True, store__isnull=True)
    else:
        return False

    bindings = bindings.filter(scope_q)
    return bindings.filter(role__permissions__codename=permission_codename).exists()


class HasRBACPermission(BasePermission):
    """DRF permission class that enforces RBAC with scope resolution.

    Set on the viewset:
        rbac_permissions_map = {
            'list': 'companies:read',
            'retrieve': 'companies:read',
            'create': 'companies:write',
            ...
        }
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        action = getattr(view, "action", None)
        permissions_map = getattr(view, "rbac_permissions_map", {})
        permission_required = permissions_map.get(action)

        if permission_required is None:
            return False

        return check_rbac_permission(
            request.user,
            permission_required,
            tenant=getattr(request, "scope_tenant", None),
            company=getattr(request, "scope_company", None),
            store=getattr(request, "scope_store", None),
        )
