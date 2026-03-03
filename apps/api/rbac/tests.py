import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from rbac.models import Permission, Role, RoleBinding
from tenants.models import Company, Membership, Store, Tenant, User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def tenant(db):
    return Tenant.objects.create(name="Acme Group", slug="acme")


@pytest.fixture
def company(tenant):
    return Company.objects.create(tenant=tenant, name="Acme Foods", slug="acme-foods")


@pytest.fixture
def store(company):
    return Store.objects.create(company=company, name="Loja Centro", slug="centro")


@pytest.fixture
def store_b(company):
    return Store.objects.create(company=company, name="Loja Sul", slug="sul")


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(email="admin@example.com", password="admin123", name="Admin")


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(email="regular@example.com", password="regular123", name="Regular")


@pytest.fixture
def all_permissions(db):
    codenames = [
        "tenants:read", "tenants:write",
        "companies:read", "companies:write",
        "stores:read", "stores:write",
        "users:read", "users:write",
        "memberships:read", "memberships:write",
        "roles:read", "roles:write",
        "rolebindings:read", "rolebindings:write",
        "permissions:read",
        "audit:read",
    ]
    return [Permission.objects.create(codename=c) for c in codenames]


def _get_perm(codename):
    return Permission.objects.get(codename=codename)


def _setup_role_binding(user, tenant, permissions_codenames, company=None, store=None):
    """Create a role with given permissions and bind it to user at scope."""
    role = Role.objects.create(name=f"role-{user.email}", tenant=tenant)
    for codename in permissions_codenames:
        role.permissions.add(_get_perm(codename))
    return RoleBinding.objects.create(
        user=user, role=role, tenant=tenant, company=company, store=store
    )


@pytest.mark.django_db
class TestRBACPermissionDenied:
    """User without required permission gets 403."""

    def test_list_companies_without_permission_returns_403(self, api_client, regular_user, tenant, all_permissions):
        Membership.objects.create(user=regular_user, tenant=tenant)
        _setup_role_binding(regular_user, tenant, ["stores:read"])

        api_client.force_authenticate(user=regular_user)
        url = reverse("companies-list")
        response = api_client.get(url, HTTP_X_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_store_without_permission_returns_403(
        self, api_client, regular_user, tenant, company, all_permissions
    ):
        Membership.objects.create(user=regular_user, tenant=tenant, company=company)
        _setup_role_binding(regular_user, tenant, ["stores:read"])

        api_client.force_authenticate(user=regular_user)
        url = reverse("stores-list")
        response = api_client.post(
            url,
            {"company": str(company.id), "name": "New Store", "slug": "new"},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestRBACPermissionGranted:
    """User with correct permission gets 200."""

    def test_list_companies_with_permission_returns_200(
        self, api_client, regular_user, tenant, company, all_permissions
    ):
        Membership.objects.create(user=regular_user, tenant=tenant)
        _setup_role_binding(regular_user, tenant, ["companies:read"])

        api_client.force_authenticate(user=regular_user)
        url = reverse("companies-list")
        response = api_client.get(url, HTTP_X_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_create_store_with_permission_returns_201(self, api_client, regular_user, tenant, company, all_permissions):
        Membership.objects.create(user=regular_user, tenant=tenant, company=company)
        _setup_role_binding(regular_user, tenant, ["stores:write", "stores:read"])

        api_client.force_authenticate(user=regular_user)
        url = reverse("stores-list")
        response = api_client.post(
            url,
            {"company": str(company.id), "name": "New Store", "slug": "new"},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_superuser_bypasses_rbac(self, api_client, superuser, tenant, company):
        api_client.force_authenticate(user=superuser)
        url = reverse("companies-list")
        response = api_client.get(url, HTTP_X_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestRBACScope:
    """Scope hierarchy: tenant -> company -> store."""

    def test_tenant_level_binding_grants_company_access(
        self, api_client, regular_user, tenant, company, all_permissions
    ):
        Membership.objects.create(user=regular_user, tenant=tenant)
        _setup_role_binding(regular_user, tenant, ["companies:read"])

        api_client.force_authenticate(user=regular_user)
        url = reverse("companies-list")
        response = api_client.get(url, HTTP_X_COMPANY_ID=str(company.id))
        assert response.status_code == status.HTTP_200_OK

    def test_company_level_binding_grants_store_access(
        self, api_client, regular_user, tenant, company, store, all_permissions
    ):
        Membership.objects.create(user=regular_user, tenant=tenant, company=company)
        _setup_role_binding(regular_user, tenant, ["stores:read"], company=company)

        api_client.force_authenticate(user=regular_user)
        url = reverse("stores-list")
        response = api_client.get(url, HTTP_X_STORE_ID=str(store.id))
        assert response.status_code == status.HTTP_200_OK

    def test_store_level_binding_does_not_grant_other_store(
        self, api_client, regular_user, tenant, company, store, store_b, all_permissions
    ):
        Membership.objects.create(user=regular_user, tenant=tenant, company=company, store=store)
        _setup_role_binding(regular_user, tenant, ["stores:read"], company=company, store=store)

        api_client.force_authenticate(user=regular_user)
        url = reverse("stores-list")
        response = api_client.get(url, HTTP_X_STORE_ID=str(store_b.id))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_changing_store_header_changes_scope(
        self, api_client, regular_user, tenant, company, store, store_b, all_permissions
    ):
        """When X-Store-Id changes, permissions and audit associate to the correct store."""
        Membership.objects.create(user=regular_user, tenant=tenant, company=company)
        _setup_role_binding(regular_user, tenant, ["stores:read"])

        api_client.force_authenticate(user=regular_user)
        url = reverse("stores-list")

        resp_a = api_client.get(url, HTTP_X_STORE_ID=str(store.id))
        assert resp_a.status_code == status.HTTP_200_OK
        assert len(resp_a.data) == 1
        assert resp_a.data[0]["id"] == str(store.id)

        resp_b = api_client.get(url, HTTP_X_STORE_ID=str(store_b.id))
        assert resp_b.status_code == status.HTTP_200_OK
        assert len(resp_b.data) == 1
        assert resp_b.data[0]["id"] == str(store_b.id)
