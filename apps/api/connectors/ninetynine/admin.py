from django.contrib import admin

from .models import NinetyNineStoreCredential


@admin.register(NinetyNineStoreCredential)
class NinetyNineStoreCredentialAdmin(admin.ModelAdmin):
    list_display = ["store", "merchant_id", "is_active", "token_expires_at", "updated_at"]
    list_filter = ["is_active"]
    search_fields = ["merchant_id", "store__name"]
    readonly_fields = ["id", "created_at", "updated_at"]
    exclude = ["client_secret", "access_token"]
