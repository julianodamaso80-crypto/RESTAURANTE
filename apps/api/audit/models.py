import uuid

from django.db import models


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        "tenants.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_events"
    )
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_events"
    )
    company = models.ForeignKey(
        "tenants.Company", on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_events"
    )
    store = models.ForeignKey(
        "tenants.Store", on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_events"
    )
    action = models.CharField(max_length=100, db_index=True)
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=100)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} on {self.entity_type}:{self.entity_id}"
