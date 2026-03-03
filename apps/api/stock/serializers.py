from rest_framework import serializers

from .models import BillOfMaterials, StockAlert, StockItem, StockLevel, StockMovement


class StockLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockLevel
        fields = ["current_quantity", "is_below_minimum", "last_movement_at", "calculated_at"]


class StockItemSerializer(serializers.ModelSerializer):
    level = StockLevelSerializer(read_only=True)

    class Meta:
        model = StockItem
        fields = ["id", "name", "unit", "minimum_stock", "is_active", "notes", "level", "created_at"]
        read_only_fields = ["id", "created_at"]


class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = ["id", "stock_item", "type", "quantity", "notes", "reference_type", "reference_id", "occurred_at"]
        read_only_fields = ["id", "occurred_at"]

    def validate_quantity(self, value):
        from .models import MovementType

        move_type = self.initial_data.get("type")
        if move_type == MovementType.SAIDA and value > 0:
            return -value  # garantir negativo para saída
        if move_type == MovementType.ENTRADA and value < 0:
            raise serializers.ValidationError("Entrada deve ter quantidade positiva.")
        return value

    def create(self, validated_data):
        movement = super().create(validated_data)
        # Recalcular saldo assincronamente
        from .tasks import recalculate_stock_level

        recalculate_stock_level.delay(str(movement.stock_item_id))
        return movement


class StockAlertSerializer(serializers.ModelSerializer):
    stock_item_name = serializers.CharField(source="stock_item.name", read_only=True)
    stock_item_unit = serializers.CharField(source="stock_item.unit", read_only=True)

    class Meta:
        model = StockAlert
        fields = [
            "id",
            "stock_item",
            "stock_item_name",
            "stock_item_unit",
            "current_qty",
            "minimum_qty",
            "is_resolved",
            "created_at",
            "resolved_at",
        ]
        read_only_fields = ["id", "created_at", "resolved_at", "stock_item_name", "stock_item_unit"]


class BillOfMaterialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillOfMaterials
        fields = ["id", "product", "stock_item", "quantity_per_unit", "is_active"]
        read_only_fields = ["id"]
