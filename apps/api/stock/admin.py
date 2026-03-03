from django.contrib import admin
from django.utils.html import format_html

from .models import BillOfMaterials, StockAlert, StockItem, StockLevel, StockMovement


class StockLevelInline(admin.TabularInline):
    model = StockLevel
    extra = 0
    readonly_fields = ["current_quantity", "is_below_minimum", "last_movement_at", "calculated_at"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class BOMInline(admin.TabularInline):
    model = BillOfMaterials
    extra = 1
    fields = ["product", "stock_item", "quantity_per_unit", "is_active"]


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ["name", "store", "unit", "current_qty_display", "minimum_stock", "alert_status", "is_active"]
    list_filter = ["unit", "is_active", "store__company__tenant"]
    search_fields = ["name", "store__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [StockLevelInline]

    actions = ["recalculate_levels"]

    def current_qty_display(self, obj):
        try:
            level = obj.level
            qty = level.current_quantity
            below = level.is_below_minimum
            color = "#f87171" if below else "#10b981"
            return format_html(
                '<span style="color:{};font-weight:bold">{} {}</span>',
                color,
                qty,
                obj.get_unit_display(),
            )
        except StockLevel.DoesNotExist:
            return "-"

    current_qty_display.short_description = "Saldo atual"

    def alert_status(self, obj):
        has_alert = StockAlert.objects.filter(stock_item=obj, is_resolved=False).exists()
        if has_alert:
            return format_html('<span style="color:#f87171">Abaixo do minimo</span>')
        return format_html('<span style="color:#10b981">OK</span>')

    alert_status.short_description = "Alerta"

    @admin.action(description="Recalcular saldo dos itens selecionados")
    def recalculate_levels(self, request, queryset):
        from .tasks import recalculate_stock_level

        for item in queryset:
            recalculate_stock_level.delay(str(item.id))
        self.message_user(request, f"{queryset.count()} recalculos enfileirados.")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ["stock_item", "type", "quantity_display", "store", "reference_type", "occurred_at"]
    list_filter = ["type", "store__company__tenant"]
    search_fields = ["stock_item__name", "reference_id"]
    readonly_fields = [
        "id",
        "stock_item",
        "store",
        "type",
        "quantity",
        "notes",
        "reference_type",
        "reference_id",
        "occurred_at",
        "created_by",
    ]
    date_hierarchy = "occurred_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def quantity_display(self, obj):
        color = "#10b981" if obj.quantity > 0 else "#f87171"
        sign = "+" if obj.quantity > 0 else ""
        return format_html(
            '<span style="color:{}">{}{} {}</span>',
            color,
            sign,
            obj.quantity,
            obj.stock_item.get_unit_display(),
        )

    quantity_display.short_description = "Quantidade"


@admin.register(StockLevel)
class StockLevelAdmin(admin.ModelAdmin):
    list_display = ["stock_item", "current_quantity", "is_below_minimum", "last_movement_at", "calculated_at"]
    readonly_fields = ["id", "stock_item", "current_quantity", "is_below_minimum", "last_movement_at", "calculated_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ["stock_item", "store", "current_qty", "minimum_qty", "is_resolved", "created_at"]
    list_filter = ["is_resolved", "store__company__tenant"]
    readonly_fields = ["id", "stock_item", "store", "current_qty", "minimum_qty", "created_at", "resolved_at"]

    actions = ["resolve_alerts"]

    @admin.action(description="Resolver alertas selecionados")
    def resolve_alerts(self, request, queryset):
        from django.utils import timezone

        updated = queryset.filter(is_resolved=False).update(is_resolved=True, resolved_at=timezone.now())
        self.message_user(request, f"{updated} alertas resolvidos.")


@admin.register(BillOfMaterials)
class BillOfMaterialsAdmin(admin.ModelAdmin):
    list_display = ["product", "stock_item", "quantity_per_unit", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["product__name", "stock_item__name"]
