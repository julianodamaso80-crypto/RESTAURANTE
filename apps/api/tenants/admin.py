from django.contrib import admin

from .models import Company, Membership, Store, Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "company_count", "store_count", "is_active", "created_at"]
    search_fields = ["name", "slug"]
    list_filter = ["is_active"]
    readonly_fields = ["id", "created_at", "updated_at"]

    def company_count(self, obj):
        return obj.companies.count()

    company_count.short_description = "Empresas"

    def store_count(self, obj):
        return Store.objects.filter(company__tenant=obj).count()

    store_count.short_description = "Lojas"


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "tenant", "store_count", "is_active", "created_at"]
    list_filter = ["tenant", "is_active"]
    search_fields = ["name", "tenant__name"]
    readonly_fields = ["id", "created_at", "updated_at"]

    def store_count(self, obj):
        return obj.stores.count()

    store_count.short_description = "Lojas"


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "tenant_name", "is_active", "created_at"]
    list_filter = ["company__tenant", "is_active"]
    search_fields = ["name", "company__name"]
    readonly_fields = ["id", "created_at", "updated_at"]

    def tenant_name(self, obj):
        return obj.company.tenant.name

    tenant_name.short_description = "Tenant"


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "tenant", "company", "store", "is_active", "created_at"]
    list_filter = ["is_active", "tenant"]
    search_fields = ["user__email", "tenant__name", "store__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
