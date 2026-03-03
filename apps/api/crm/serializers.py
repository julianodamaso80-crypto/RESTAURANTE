from rest_framework import serializers

from .models import (
    Campaign,
    CampaignRun,
    CampaignTemplate,
    CustomerSegment,
    TenantBillingQuota,
)
from .segmentation import estimate_segment_size


class CustomerSegmentSerializer(serializers.ModelSerializer):
    estimated_size = serializers.SerializerMethodField()

    class Meta:
        model = CustomerSegment
        fields = ["id", "name", "description", "criteria", "estimated_size", "created_at"]
        read_only_fields = ["id", "created_at", "estimated_size"]

    def get_estimated_size(self, obj):
        return estimate_segment_size(obj)


class CampaignTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignTemplate
        fields = ["id", "name", "channel", "subject", "body", "created_at"]
        read_only_fields = ["id", "created_at"]


class CampaignRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignRun
        fields = [
            "id",
            "status",
            "started_at",
            "completed_at",
            "total_recipients",
            "sent_count",
            "delivered_count",
            "failed_count",
            "opted_out_count",
            "error_detail",
        ]
        read_only_fields = fields


class CampaignSerializer(serializers.ModelSerializer):
    runs = CampaignRunSerializer(many=True, read_only=True)
    segment_name = serializers.CharField(source="segment.name", read_only=True)
    template_name = serializers.CharField(source="template.name", read_only=True)

    class Meta:
        model = Campaign
        fields = [
            "id",
            "name",
            "status",
            "segment",
            "segment_name",
            "template",
            "template_name",
            "scheduled_at",
            "runs",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BillingQuotaSerializer(serializers.ModelSerializer):
    usage_pct = serializers.FloatField(read_only=True)
    is_blocked = serializers.BooleanField(read_only=True)
    is_near_limit = serializers.BooleanField(read_only=True)

    class Meta:
        model = TenantBillingQuota
        fields = [
            "max_contacts",
            "current_period_contacts",
            "usage_pct",
            "is_blocked",
            "is_near_limit",
            "period_start",
            "updated_at",
        ]
        read_only_fields = fields
