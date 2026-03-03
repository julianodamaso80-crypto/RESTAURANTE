from django.contrib import admin

from .models import ConsentRecord, Customer, CustomerEvent, CustomerIdentity


class CustomerIdentityInline(admin.TabularInline):
    model = CustomerIdentity
    extra = 0
    readonly_fields = ["id", "type", "value", "is_verified", "source", "created_at"]
    can_delete = False


class ConsentRecordInline(admin.TabularInline):
    model = ConsentRecord
    extra = 0
    readonly_fields = ["id", "channel", "status", "source", "created_at"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        "name_or_phone",
        "tenant",
        "rfv_frequency",
        "rfv_monetary_display",
        "rfv_recency_days",
        "is_active",
    ]
    list_filter = ["is_active", "tenant"]
    search_fields = ["name", "phone", "email"]
    readonly_fields = [
        "id",
        "rfv_recency_days",
        "rfv_frequency",
        "rfv_monetary_cents",
        "rfv_last_order_at",
        "rfv_calculated_at",
        "created_at",
        "updated_at",
    ]
    inlines = [CustomerIdentityInline, ConsentRecordInline]

    actions = ["trigger_rfv_recalculation"]

    def name_or_phone(self, obj):
        return obj.name or obj.phone or str(obj.id)[:8]

    name_or_phone.short_description = "Cliente"

    def rfv_monetary_display(self, obj):
        return f"R$ {obj.rfv_monetary_cents / 100:.2f}"

    rfv_monetary_display.short_description = "Gasto total"

    @admin.action(description="Recalcular RFV dos clientes selecionados")
    def trigger_rfv_recalculation(self, request, queryset):
        from .tasks import recalculate_customer_rfv

        for customer in queryset:
            recalculate_customer_rfv.delay(str(customer.id))
        self.message_user(request, f"{queryset.count()} recalculos enfileirados.")


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ["customer", "channel", "status", "source", "created_at"]
    list_filter = ["channel", "status"]
    readonly_fields = [
        "id",
        "customer",
        "channel",
        "status",
        "source",
        "ip_address",
        "user_agent",
        "legal_basis",
        "created_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CustomerEvent)
class CustomerEventAdmin(admin.ModelAdmin):
    list_display = ["customer", "event_type", "store", "occurred_at"]
    list_filter = ["event_type"]
    readonly_fields = ["id", "customer", "event_type", "store", "payload", "occurred_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
