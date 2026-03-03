from rest_framework import serializers

from audit.models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = [
            "id",
            "actor",
            "tenant",
            "company",
            "store",
            "action",
            "entity_type",
            "entity_id",
            "metadata",
            "created_at",
        ]
