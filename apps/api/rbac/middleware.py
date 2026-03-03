from tenants.models import Company, Store, Tenant


class ScopeMiddleware:
    """Resolve multi-tenant scope from request headers.

    Headers:
        X-Tenant-Id: UUID of the tenant
        X-Company-Id: UUID of the company (auto-resolves tenant)
        X-Store-Id: UUID of the store (auto-resolves company and tenant)

    Priority: X-Store-Id > X-Company-Id > X-Tenant-Id.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.scope_tenant = None
        request.scope_company = None
        request.scope_store = None

        store_id = request.META.get("HTTP_X_STORE_ID")
        company_id = request.META.get("HTTP_X_COMPANY_ID")
        tenant_id = request.META.get("HTTP_X_TENANT_ID")

        if store_id:
            try:
                store = Store.objects.select_related("company__tenant").get(id=store_id, is_active=True)
                request.scope_store = store
                request.scope_company = store.company
                request.scope_tenant = store.company.tenant
            except (Store.DoesNotExist, ValueError):
                pass
        elif company_id:
            try:
                company = Company.objects.select_related("tenant").get(id=company_id, is_active=True)
                request.scope_company = company
                request.scope_tenant = company.tenant
            except (Company.DoesNotExist, ValueError):
                pass
        elif tenant_id:
            try:
                request.scope_tenant = Tenant.objects.get(id=tenant_id, is_active=True)
            except (Tenant.DoesNotExist, ValueError):
                pass

        return self.get_response(request)
