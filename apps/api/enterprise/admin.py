from django.contrib import admin

from .models import FranchiseeOnboarding, FranchiseTemplate, NetworkAlert, NetworkReport, StoreOverride


@admin.register(FranchiseTemplate)
class FranchiseTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "company__name"]


@admin.register(StoreOverride)
class StoreOverrideAdmin(admin.ModelAdmin):
    list_display = ["store", "template", "created_at"]
    search_fields = ["store__name"]


@admin.register(FranchiseeOnboarding)
class FranchiseeOnboardingAdmin(admin.ModelAdmin):
    list_display = ["store", "template", "status", "created_at", "completed_at"]
    list_filter = ["status"]
    search_fields = ["store__name"]


@admin.register(NetworkReport)
class NetworkReportAdmin(admin.ModelAdmin):
    list_display = ["company", "period", "date_from", "date_to", "generated_at"]
    list_filter = ["period"]
    search_fields = ["company__name"]


@admin.register(NetworkAlert)
class NetworkAlertAdmin(admin.ModelAdmin):
    list_display = ["company", "store", "alert_type", "is_resolved", "created_at"]
    list_filter = ["alert_type", "is_resolved"]
    search_fields = ["store__name", "company__name"]
