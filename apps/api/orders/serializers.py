import random

from django.db import transaction
from rest_framework import serializers

from .enums import OrderChannel, OrderStatus, OrderType, PaymentMethod
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
            "customer_name",
            "customer_phone",
            "customer_email",
            "delivery_address",
            "payment_method",
            "change_for_cents",
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


# --- Public (own-channel) serializers ---


class PublicOrderItemCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    quantity = serializers.IntegerField(min_value=1)
    unit_price_cents = serializers.IntegerField(min_value=0)
    total_cents = serializers.IntegerField(min_value=0)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    modifiers_summary = serializers.CharField(required=False, allow_blank=True, default="")


class PublicOrderCreateSerializer(serializers.Serializer):
    catalog_id = serializers.UUIDField()
    customer_name = serializers.CharField(max_length=255)
    customer_phone = serializers.CharField(max_length=30)
    customer_email = serializers.EmailField(required=False, allow_blank=True, default="")
    order_type = serializers.ChoiceField(choices=OrderType.choices)
    delivery_address = serializers.JSONField(required=False, default=None)
    payment_method = serializers.ChoiceField(choices=PaymentMethod.choices)
    change_for_cents = serializers.IntegerField(required=False, allow_null=True, default=None)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    items = PublicOrderItemCreateSerializer(many=True)
    idempotency_key = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Pedido deve ter pelo menos 1 item.")
        return value

    def validate(self, attrs):
        if attrs["order_type"] == OrderType.DELIVERY and not attrs.get("delivery_address"):
            raise serializers.ValidationError({"delivery_address": "Endereço é obrigatório para delivery."})
        if attrs["payment_method"] == PaymentMethod.CASH and not attrs.get("change_for_cents"):
            pass  # change_for_cents is optional even for cash (exact amount)
        return attrs

    def create(self, validated_data):
        from catalog.models import Catalog

        items_data = validated_data.pop("items")
        catalog_id = validated_data.pop("catalog_id")
        idempotency_key_value = validated_data.pop("idempotency_key", None)

        try:
            catalog = Catalog.objects.select_related("store__company__tenant").get(pk=catalog_id)
        except Catalog.DoesNotExist:
            raise serializers.ValidationError({"catalog_id": "Catálogo não encontrado."})

        store = catalog.store
        if not store:
            raise serializers.ValidationError({"catalog_id": "Catálogo sem loja associada."})
        tenant = store.company.tenant

        # Idempotency check
        if idempotency_key_value:
            existing = IdempotencyKey.objects.filter(tenant=tenant, key=idempotency_key_value).first()
            if existing and existing.order:
                return existing.order

        # Calculate totals
        subtotal_cents = sum(item["total_cents"] for item in items_data)
        delivery_fee_cents = 0  # TODO: calculate based on address/store config
        discount_cents = 0
        total_cents = subtotal_cents + delivery_fee_cents - discount_cents

        display_number = f"#{random.randint(1, 9999):04d}"

        with transaction.atomic():
            order = Order.objects.create(
                tenant=tenant,
                store=store,
                display_number=display_number,
                channel=OrderChannel.OWN,
                order_type=validated_data["order_type"],
                customer_name=validated_data["customer_name"],
                customer_phone=validated_data["customer_phone"],
                customer_email=validated_data.get("customer_email", ""),
                delivery_address=validated_data.get("delivery_address"),
                payment_method=validated_data["payment_method"],
                change_for_cents=validated_data.get("change_for_cents"),
                notes=validated_data.get("notes", ""),
                subtotal_cents=subtotal_cents,
                delivery_fee_cents=delivery_fee_cents,
                discount_cents=discount_cents,
                total_cents=total_cents,
            )

            for item_data in items_data:
                modifiers_summary = item_data.pop("modifiers_summary", "")
                item_notes = item_data.get("notes", "")
                if modifiers_summary:
                    item_notes = (
                        f"{modifiers_summary}\n{item_notes}".strip() if item_notes else modifiers_summary
                    )
                filtered = {k: v for k, v in item_data.items() if k != "notes"}
                OrderItem.objects.create(order=order, notes=item_notes, **filtered)

            if idempotency_key_value:
                IdempotencyKey.objects.get_or_create(
                    tenant=tenant,
                    key=idempotency_key_value,
                    defaults={"order": order},
                )

        return order


class PublicOrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "display_number",
            "channel",
            "order_type",
            "status",
            "customer_name",
            "customer_phone",
            "subtotal_cents",
            "discount_cents",
            "delivery_fee_cents",
            "total_cents",
            "payment_method",
            "notes",
            "created_at",
            "updated_at",
            "confirmed_at",
            "delivered_at",
            "cancelled_at",
            "items",
        ]
