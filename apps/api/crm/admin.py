from django.contrib import admin
from django.utils.html import format_html

from .models import Campaign, CampaignRecipient, CampaignRun, CampaignTemplate, CustomerSegment, TenantBillingQuota


class CampaignRunInline(admin.TabularInline):
    model = CampaignRun
    extra = 0
    readonly_fields = ["id", "status", "started_at", "completed_at", "total_recipients", "sent_count", "failed_count"]
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(CustomerSegment)
class CustomerSegmentAdmin(admin.ModelAdmin):
    list_display = ["name", "tenant", "criteria_count", "estimated_size", "created_at"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]

    def criteria_count(self, obj):
        return len(obj.criteria)

    criteria_count.short_description = "Criterios"

    def estimated_size(self, obj):
        from .segmentation import estimate_segment_size

        return estimate_segment_size(obj)

    estimated_size.short_description = "Clientes"


@admin.register(CampaignTemplate)
class CampaignTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "tenant", "channel", "created_at"]
    list_filter = ["channel"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ["name", "tenant", "status", "segment", "template", "created_at"]
    list_filter = ["status", "tenant"]
    search_fields = ["name"]
    inlines = [CampaignRunInline]
    readonly_fields = ["id", "created_at", "updated_at"]

    actions = ["launch_campaigns"]

    @admin.action(description="Lancar campanhas selecionadas")
    def launch_campaigns(self, request, queryset):
        from .models import CampaignStatus
        from .tasks import execute_campaign_run

        launched = 0
        for campaign in queryset.filter(status__in=[CampaignStatus.DRAFT, CampaignStatus.SCHEDULED]):
            run = CampaignRun.objects.create(campaign=campaign)
            campaign.status = CampaignStatus.RUNNING
            campaign.save(update_fields=["status"])
            execute_campaign_run.delay(str(run.id))
            launched += 1
        self.message_user(request, f"{launched} campanhas lancadas.")


@admin.register(CampaignRun)
class CampaignRunAdmin(admin.ModelAdmin):
    list_display = ["campaign", "status", "total_recipients", "sent_count", "failed_count", "started_at"]
    list_filter = ["status"]
    readonly_fields = [
        "id",
        "campaign",
        "started_at",
        "completed_at",
        "total_recipients",
        "sent_count",
        "delivered_count",
        "failed_count",
        "opted_out_count",
        "error_detail",
    ]

    def has_add_permission(self, request):
        return False


@admin.register(CampaignRecipient)
class CampaignRecipientAdmin(admin.ModelAdmin):
    list_display = ["run", "customer", "status", "channel", "destination", "sent_at"]
    list_filter = ["status", "channel"]
    readonly_fields = ["id", "run", "customer", "status", "channel", "destination", "sent_at", "error_detail"]


@admin.register(TenantBillingQuota)
class TenantBillingQuotaAdmin(admin.ModelAdmin):
    list_display = ["tenant", "usage_display", "is_blocked_display", "is_near_limit_display", "period_start"]
    readonly_fields = [
        "id",
        "current_period_contacts",
        "updated_at",
    ]

    def usage_display(self, obj):
        pct = obj.usage_pct
        color = "#f87171" if obj.is_blocked else ("#fbbf24" if obj.is_near_limit else "#10b981")
        return format_html(
            '<span style="color:{}">{}/{} ({:.1f}%)</span>',
            color,
            obj.current_period_contacts,
            obj.max_contacts,
            pct,
        )

    usage_display.short_description = "Uso"

    def is_blocked_display(self, obj):
        return obj.is_blocked

    is_blocked_display.boolean = True
    is_blocked_display.short_description = "Bloqueado"

    def is_near_limit_display(self, obj):
        return obj.is_near_limit

    is_near_limit_display.boolean = True
    is_near_limit_display.short_description = "Perto do limite"
