from django.contrib import admin

from .models import RappiStoreCredential


@admin.register(RappiStoreCredential)
class RappiStoreCredentialAdmin(admin.ModelAdmin):
    list_display = ["store", "rappi_store_id", "environment", "is_active", "updated_at"]
    list_filter = ["is_active", "environment"]
    search_fields = ["rappi_store_id", "store__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    exclude = ["rappi_token"]
