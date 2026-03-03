from django.contrib import admin

from .models import Catalog, Category, ModifierGroup, ModifierOption, Product, ProductAvailability, ProductChannelMap


class ModifierOptionInline(admin.TabularInline):
    model = ModifierOption
    extra = 1


class ProductChannelMapInline(admin.TabularInline):
    model = ProductChannelMap
    extra = 0


class ProductAvailabilityInline(admin.TabularInline):
    model = ProductAvailability
    extra = 0


class ProductInline(admin.TabularInline):
    model = Product
    extra = 0
    show_change_link = True
    fields = ["name", "price_cents", "status", "display_order"]


@admin.register(Catalog)
class CatalogAdmin(admin.ModelAdmin):
    list_display = ["name", "store", "status", "channels", "display_order"]
    list_filter = ["status", "store__company__tenant"]
    search_fields = ["name", "store__name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "catalog", "status", "display_order"]
    list_filter = ["status", "catalog__store__company__tenant"]
    search_fields = ["name"]
    inlines = [ProductInline]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price_display", "status", "display_order"]
    list_filter = ["status", "category__catalog__store__company__tenant"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [ModifierOptionInline, ProductChannelMapInline, ProductAvailabilityInline]

    def price_display(self, obj):
        return f"R$ {obj.price_cents / 100:.2f}"

    price_display.short_description = "Preco"


@admin.register(ModifierGroup)
class ModifierGroupAdmin(admin.ModelAdmin):
    list_display = ["name", "product", "min_choices", "max_choices", "is_active"]
    list_filter = ["is_active"]
    inlines = [ModifierOptionInline]


@admin.register(ModifierOption)
class ModifierOptionAdmin(admin.ModelAdmin):
    list_display = ["name", "group", "price_delta_cents", "is_active"]
    list_filter = ["is_active"]


@admin.register(ProductChannelMap)
class ProductChannelMapAdmin(admin.ModelAdmin):
    list_display = ["product", "channel", "external_id", "is_active"]
    list_filter = ["channel", "is_active"]
    search_fields = ["external_id"]


@admin.register(ProductAvailability)
class ProductAvailabilityAdmin(admin.ModelAdmin):
    list_display = ["product", "week_day", "start_time", "end_time"]
    list_filter = ["week_day"]
