from django.contrib import admin

from .models import AuditEvent

# Customizar titulo do admin
admin.site.site_header = "Restaurante ERP - Admin"
admin.site.site_title = "Restaurante ERP"
admin.site.index_title = "Painel de Operacao"


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ["tenant", "store", "actor", "action", "entity_type", "entity_id", "created_at"]
    list_filter = ["action", "entity_type"]
    search_fields = ["actor__email", "entity_id", "entity_type"]
    readonly_fields = [f.name for f in AuditEvent._meta.get_fields() if hasattr(f, "name")]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
