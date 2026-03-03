from django.contrib import admin
from django.utils.html import format_html

from .models import IFoodStoreCredential, RawEvent, RawEventStatus


@admin.register(RawEvent)
class RawEventAdmin(admin.ModelAdmin):
    list_display = ["event_id", "event_type", "source", "status_badge", "retry_count", "received_at"]
    list_filter = ["status", "source", "event_type"]
    search_fields = ["event_id"]
    readonly_fields = [
        "id",
        "source",
        "event_id",
        "event_type",
        "tenant_id",
        "store_id",
        "payload",
        "headers",
        "status",
        "error_detail",
        "retry_count",
        "received_at",
        "processed_at",
    ]
    date_hierarchy = "received_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def status_badge(self, obj):
        colors = {
            RawEventStatus.RECEIVED: "#fbbf24",
            RawEventStatus.ENQUEUED: "#60a5fa",
            RawEventStatus.PROCESSING: "#a78bfa",
            RawEventStatus.PROCESSED: "#10b981",
            RawEventStatus.DUPLICATE: "#9ca3af",
            RawEventStatus.FAILED: "#f87171",
        }
        color = colors.get(obj.status, "#9ca3af")
        return format_html(
            '<span style="background:{};padding:2px 8px;border-radius:4px;color:#fff;font-size:11px">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"

    actions = ["reprocess_events"]

    @admin.action(description="Reprocessar eventos selecionados")
    def reprocess_events(self, request, queryset):
        from .tasks import process_ifood_event

        failed = queryset.filter(status__in=[RawEventStatus.FAILED])
        count = 0
        for event in failed:
            process_ifood_event.delay(str(event.id))
            count += 1
        self.message_user(request, f"{count} eventos enfileirados para reprocessamento.")


@admin.register(IFoodStoreCredential)
class IFoodStoreCredentialAdmin(admin.ModelAdmin):
    list_display = ["store", "merchant_id", "is_active", "token_expires_at", "updated_at"]
    list_filter = ["is_active"]
    search_fields = ["merchant_id", "store__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    exclude = ["client_secret", "access_token"]
