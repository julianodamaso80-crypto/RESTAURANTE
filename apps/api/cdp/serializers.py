from rest_framework import serializers

from .consent import has_consent
from .models import ConsentChannel, ConsentRecord, Customer, CustomerEvent, CustomerIdentity


class CustomerIdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerIdentity
        fields = ["id", "type", "value", "is_verified", "source", "created_at"]
        read_only_fields = ["id", "created_at"]


class ConsentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsentRecord
        fields = ["id", "channel", "status", "source", "legal_basis", "created_at"]
        read_only_fields = ["id", "created_at"]


class CustomerEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerEvent
        fields = ["id", "event_type", "payload", "occurred_at"]
        read_only_fields = ["id", "occurred_at"]


class CustomerSerializer(serializers.ModelSerializer):
    identities = CustomerIdentitySerializer(many=True, read_only=True)
    consent_summary = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "phone",
            "email",
            "rfv_recency_days",
            "rfv_frequency",
            "rfv_monetary_cents",
            "rfv_last_order_at",
            "rfv_calculated_at",
            "is_active",
            "is_anonymous",
            "identities",
            "consent_summary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "rfv_recency_days",
            "rfv_frequency",
            "rfv_monetary_cents",
            "rfv_last_order_at",
            "rfv_calculated_at",
        ]

    def get_consent_summary(self, obj):
        return {channel: has_consent(obj, channel) for channel in ConsentChannel.values}


class ConsentUpdateSerializer(serializers.Serializer):
    channel = serializers.ChoiceField(choices=ConsentChannel.choices)
    action = serializers.ChoiceField(choices=["grant", "revoke"])
    source = serializers.CharField(required=False, default="api")
    legal_basis = serializers.CharField(required=False, default="")
