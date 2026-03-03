from django.db import transaction
from rest_framework import serializers

from .enums import OrderStatus
from .models import IdempotencyKey, Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "name", "external_item_id", "quantity", "unit_price_cents", "total_cents", "notes"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "display_number",
            "channel",
            "order_type",
            "external_id",
            "status",
            "subtotal_cents",
            "discount_cents",
            "delivery_fee_cents",
            "total_cents",
            "created_at",
            "updated_at",
            "confirmed_at",
            "delivered_at",
            "cancelled_at",
            "notes",
            "items",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "status", "confirmed_at", "delivered_at", "cancelled_at"]


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, required=True)
    idempotency_key = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Order
        fields = [
            "display_number",
            "channel",
            "order_type",
            "external_id",
            "subtotal_cents",
            "discount_cents",
            "delivery_fee_cents",
            "total_cents",
            "notes",
            "items",
            "idempotency_key",
        ]

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        idempotency_key_value = validated_data.pop("idempotency_key", None)

        tenant = self.context["request"].scope_tenant
        store = self.context["request"].scope_store

        # Idempotency check
        if idempotency_key_value:
            existing = IdempotencyKey.objects.filter(tenant=tenant, key=idempotency_key_value).first()
            if existing and existing.order:
                return existing.order

        with transaction.atomic():
            order = Order.objects.create(tenant=tenant, store=store, **validated_data)
            for item_data in items_data:
                OrderItem.objects.create(order=order, **item_data)

            if idempotency_key_value:
                IdempotencyKey.objects.get_or_create(
                    tenant=tenant,
                    key=idempotency_key_value,
                    defaults={"order": order},
                )

        return order


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.CharField()

    def validate_status(self, value):
        try:
            OrderStatus(value)
        except ValueError:
            raise serializers.ValidationError(f"Status inválido: '{value}'.")
        return value
