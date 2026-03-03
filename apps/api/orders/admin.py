from django.contrib import admin
from django.utils.html import format_html

from .enums import OrderStatus
from .models import IdempotencyKey, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["id", "name", "quantity", "unit_price_cents", "total_cents", "notes"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["display_number", "store", "channel", "status_badge", "total_display", "created_at"]
    list_filter = ["status", "channel", "order_type", "store__company__tenant"]
    search_fields = ["display_number", "external_id", "store__name"]
    readonly_fields = ["id", "created_at", "updated_at", "confirmed_at", "delivered_at", "cancelled_at"]
    inlines = [OrderItemInline]
    date_hierarchy = "created_at"
    list_per_page = 50

    actions = ["mark_cancelled"]

    def status_badge(self, obj):
        colors = {
            OrderStatus.PENDING: "#fbbf24",
            OrderStatus.CONFIRMED: "#60a5fa",
            OrderStatus.IN_PREPARATION: "#a78bfa",
            OrderStatus.READY: "#34d399",
            OrderStatus.DISPATCHED: "#f97316",
            OrderStatus.DELIVERED: "#10b981",
            OrderStatus.CANCELLED: "#f87171",
        }
        color = colors.get(obj.status, "#9ca3af")
        return format_html(
            '<span style="background:{};padding:2px 8px;border-radius:4px;color:#fff;font-size:11px">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"

    def total_display(self, obj):
        return f"R$ {obj.total_cents / 100:.2f}"

    total_display.short_description = "Total"

    @admin.action(description="Cancelar pedidos selecionados")
    def mark_cancelled(self, request, queryset):
        from .fsm import InvalidOrderTransition

        cancelled = 0
        errors = 0
        for order in queryset:
            try:
                order.transition_to(OrderStatus.CANCELLED)
                order.save()
                cancelled += 1
            except InvalidOrderTransition:
                errors += 1
        self.message_user(request, f"{cancelled} cancelados, {errors} com erro.")


@admin.register(IdempotencyKey)
class IdempotencyKeyAdmin(admin.ModelAdmin):
    list_display = ["key", "tenant", "order", "created_at"]
    search_fields = ["key"]
    readonly_fields = ["id", "key", "tenant", "order", "created_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
