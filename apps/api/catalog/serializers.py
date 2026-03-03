from rest_framework import serializers

from .availability import is_product_available
from .models import Catalog, Category, ModifierGroup, ModifierOption, Product, ProductAvailability, ProductChannelMap


class ModifierOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModifierOption
        fields = ["id", "name", "price_delta_cents", "is_default", "is_active", "display_order"]


class ModifierGroupSerializer(serializers.ModelSerializer):
    options = ModifierOptionSerializer(many=True, read_only=True)

    class Meta:
        model = ModifierGroup
        fields = ["id", "name", "description", "min_choices", "max_choices", "display_order", "is_active", "options"]


class ProductChannelMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductChannelMap
        fields = ["id", "channel", "external_id", "external_sku", "price_override_cents", "is_active"]


class ProductAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAvailability
        fields = ["id", "week_day", "start_time", "end_time"]


class ProductSerializer(serializers.ModelSerializer):
    modifier_groups = ModifierGroupSerializer(many=True, read_only=True)
    channel_maps = ProductChannelMapSerializer(many=True, read_only=True)
    availability_windows = ProductAvailabilitySerializer(many=True, read_only=True)
    is_available_now = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "image_url",
            "price_cents",
            "status",
            "display_order",
            "tags",
            "serving_size",
            "calories",
            "is_available_now",
            "modifier_groups",
            "channel_maps",
            "availability_windows",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "is_available_now"]

    def get_is_available_now(self, obj):
        return is_product_available(obj)


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer leve para listagem (sem modifier_groups completos)."""

    is_available_now = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "price_cents", "status", "image_url", "display_order", "tags", "is_available_now"]

    def get_is_available_now(self, obj):
        return is_product_available(obj)


class CategorySerializer(serializers.ModelSerializer):
    products = ProductListSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "description", "image_url", "status", "display_order", "products"]


class CatalogSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = Catalog
        fields = ["id", "name", "status", "channels", "display_order", "categories", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class CatalogPublicSerializer(serializers.ModelSerializer):
    """Catálogo público — usado pelo canal próprio e integrações.

    Exclui mapeamentos internos. Filtra produtos inativos.
    """

    categories = serializers.SerializerMethodField()

    class Meta:
        model = Catalog
        fields = ["id", "name", "categories"]

    def get_categories(self, catalog):
        active_cats = catalog.categories.filter(status="ACTIVE").order_by("display_order")
        return [
            {
                "id": str(cat.id),
                "name": cat.name,
                "description": cat.description,
                "image_url": cat.image_url,
                "products": [
                    {
                        "id": str(p.id),
                        "name": p.name,
                        "description": p.description,
                        "image_url": p.image_url,
                        "price_cents": p.price_cents,
                        "tags": p.tags,
                        "is_available_now": is_product_available(p),
                        "modifier_groups": [
                            {
                                "id": str(mg.id),
                                "name": mg.name,
                                "min_choices": mg.min_choices,
                                "max_choices": mg.max_choices,
                                "options": [
                                    {
                                        "id": str(opt.id),
                                        "name": opt.name,
                                        "price_delta_cents": opt.price_delta_cents,
                                        "is_default": opt.is_default,
                                    }
                                    for opt in mg.options.filter(is_active=True).order_by("display_order")
                                ],
                            }
                            for mg in p.modifier_groups.filter(is_active=True).order_by("display_order")
                        ],
                    }
                    for p in cat.products.filter(status="ACTIVE").order_by("display_order")
                ],
            }
            for cat in active_cats
        ]
