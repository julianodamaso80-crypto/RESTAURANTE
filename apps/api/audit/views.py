from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from audit.models import AuditEvent
from audit.serializers import AuditEventSerializer
from rbac.permissions import HasRBACPermission


class AuditEventFilter(filters.FilterSet):
    start_date = filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    end_date = filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = AuditEvent
        fields = ["tenant", "company", "store", "action", "entity_type"]


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditEventSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    filterset_class = AuditEventFilter
    rbac_permissions_map = {
        "list": "audit:read",
        "retrieve": "audit:read",
    }

    def get_queryset(self):
        qs = AuditEvent.objects.select_related("actor", "tenant", "company", "store")
        tenant = getattr(self.request, "scope_tenant", None)
        if tenant:
            return qs.filter(tenant=tenant)
        if self.request.user.is_superuser:
            return qs.all()
        return qs.none()
