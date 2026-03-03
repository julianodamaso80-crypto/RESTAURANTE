from django.contrib import admin
from django.utils.html import format_html

from .models import KDSStation, KDSTicket, KDSTicketStatus


class KDSTicketInline(admin.TabularInline):
    model = KDSTicket
    extra = 0
    readonly_fields = [
        "order",
        "status",
        "enqueued_at",
        "started_at",
        "completed_at",
        "wait_time_seconds",
        "prep_time_seconds",
    ]
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(KDSStation)
class KDSStationAdmin(admin.ModelAdmin):
    list_display = ["name", "store", "category", "is_active", "active_tickets", "display_order"]
    list_filter = ["category", "is_active", "store__company__tenant"]
    search_fields = ["name", "store__name"]
    inlines = [KDSTicketInline]

    def active_tickets(self, obj):
        count = obj.tickets.exclude(status=KDSTicketStatus.DONE).count()
        color = "#f87171" if count > 5 else "#10b981"
        return format_html('<span style="color:{};font-weight:bold">{}</span>', color, count)

    active_tickets.short_description = "Tickets ativos"


@admin.register(KDSTicket)
class KDSTicketAdmin(admin.ModelAdmin):
    list_display = ["order", "station", "status", "enqueued_at", "wait_time_seconds", "prep_time_seconds"]
    list_filter = ["status", "station__store__company__tenant"]
    readonly_fields = ["id", "enqueued_at", "started_at", "completed_at", "wait_time_seconds", "prep_time_seconds"]
    date_hierarchy = "enqueued_at"
