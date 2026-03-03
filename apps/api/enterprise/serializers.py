from rest_framework import serializers

from .models import FranchiseeOnboarding, FranchiseTemplate, NetworkAlert, NetworkReport, StoreOverride


class FranchiseTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FranchiseTemplate
        fields = ["id", "name", "template_catalog", "default_kds_stations", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class StoreOverrideSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreOverride
        fields = [
            "id",
            "store",
            "template",
            "product_price_overrides",
            "product_status_overrides",
            "bom_overrides",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class FranchiseeOnboardingSerializer(serializers.ModelSerializer):
    class Meta:
        model = FranchiseeOnboarding
        fields = [
            "id",
            "template",
            "store",
            "status",
            "steps_completed",
            "error_detail",
            "started_at",
            "completed_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "steps_completed",
            "error_detail",
            "started_at",
            "completed_at",
            "created_at",
        ]


class NetworkReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkReport
        fields = ["id", "period", "date_from", "date_to", "data", "generated_at"]
        read_only_fields = fields


class NetworkAlertSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source="store.name", read_only=True)

    class Meta:
        model = NetworkAlert
        fields = ["id", "store", "store_name", "alert_type", "payload", "is_resolved", "created_at", "resolved_at"]
        read_only_fields = ["id", "created_at", "resolved_at"]
