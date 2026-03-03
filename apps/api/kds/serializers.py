from django.utils import timezone
from rest_framework import serializers

from .models import KDSStation, KDSTicket, KDSTicketStatus


class KDSStationSerializer(serializers.ModelSerializer):
    active_tickets_count = serializers.SerializerMethodField()

    class Meta:
        model = KDSStation
        fields = [
            "id",
            "name",
            "category",
            "is_active",
            "display_order",
            "filter_order_types",
            "active_tickets_count",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_active_tickets_count(self, obj):
        return obj.tickets.exclude(status=KDSTicketStatus.DONE).count()


class KDSTicketOrderSerializer(serializers.Serializer):
    """Minimal Order snapshot for KDS display."""

    id = serializers.UUIDField()
    display_number = serializers.CharField()
    channel = serializers.CharField()
    order_type = serializers.CharField()
    total_cents = serializers.IntegerField()
    notes = serializers.CharField()
    confirmed_at = serializers.DateTimeField()
    items = serializers.SerializerMethodField()

    def get_items(self, order):
        return [
            {
                "name": item.name,
                "quantity": item.quantity,
                "notes": item.notes,
            }
            for item in order.items.all()
        ]


class KDSTicketSerializer(serializers.ModelSerializer):
    order = KDSTicketOrderSerializer(read_only=True)
    elapsed_seconds = serializers.SerializerMethodField()

    class Meta:
        model = KDSTicket
        fields = [
            "id",
            "status",
            "order",
            "enqueued_at",
            "started_at",
            "completed_at",
            "wait_time_seconds",
            "prep_time_seconds",
            "elapsed_seconds",
            "notes",
        ]
        read_only_fields = [
            "id",
            "enqueued_at",
            "started_at",
            "completed_at",
            "wait_time_seconds",
            "prep_time_seconds",
        ]

    def get_elapsed_seconds(self, obj):
        """Seconds since enqueued (for live timer in KDS frontend)."""
        if obj.completed_at:
            return None
        return int((timezone.now() - obj.enqueued_at).total_seconds())


class KDSTicketStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            KDSTicketStatus.IN_PROGRESS,
            KDSTicketStatus.DONE,
        ]
    )
