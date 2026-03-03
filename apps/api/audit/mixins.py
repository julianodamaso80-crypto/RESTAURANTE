from audit.models import AuditEvent


class AuditMixin:
    """ViewSet mixin that auto-creates AuditEvents on create/update/destroy.

    Set `audit_entity_type` on the viewset to override the entity type label.
    Falls back to the model class name in lowercase.
    """

    audit_entity_type = None

    def _get_entity_type(self):
        if self.audit_entity_type:
            return self.audit_entity_type
        return self.queryset.model.__name__.lower()

    def _get_audit_metadata(self, request):
        return {
            "ip": request.META.get("REMOTE_ADDR", ""),
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "request_id": request.META.get("HTTP_X_REQUEST_ID", ""),
            "endpoint": request.path,
            "method": request.method,
        }

    def _create_audit_event(self, request, action, instance):
        AuditEvent.objects.create(
            actor=request.user if request.user.is_authenticated else None,
            tenant=getattr(request, "scope_tenant", None),
            company=getattr(request, "scope_company", None),
            store=getattr(request, "scope_store", None),
            action=action,
            entity_type=instance.__class__.__name__,
            entity_id=str(instance.pk),
            metadata=self._get_audit_metadata(request),
        )

    def perform_create(self, serializer):
        instance = serializer.save()
        entity = self._get_entity_type()
        self._create_audit_event(self.request, f"{entity}:create", instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        entity = self._get_entity_type()
        self._create_audit_event(self.request, f"{entity}:update", instance)

    def perform_destroy(self, instance):
        entity = self._get_entity_type()
        self._create_audit_event(self.request, f"{entity}:delete", instance)
        instance.delete()
