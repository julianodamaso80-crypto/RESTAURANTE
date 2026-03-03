import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from audit.models import AuditEvent
from rbac.models import Permission, Role, RoleBinding
from tenants.models import Company, Membership, Tenant, User


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
    role = Role.objects.create(name=f"role-{user.email}", tenant=tenant)
    for codename in permissions_codenames:
        role.permissions.add(_get_perm(codename))
    return RoleBinding.objects.create(
        user=user, role=role, tenant=tenant, company=company, store=store
    )


@pytest.mark.django_db
class TestAuditOnStoreCreate:
    """Creating a store generates an AuditEvent with action store:create."""

    def test_store_create_generates_audit_event(self, api_client, superuser, tenant, company):
        api_client.force_authenticate(user=superuser)
        url = reverse("stores-list")
        response = api_client.post(
            url,
            {"company": str(company.id), "name": "Loja Centro", "slug": "centro"},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_201_CREATED

        events = AuditEvent.objects.filter(action="store:create")
        assert events.count() == 1

        event = events.first()
        assert event.actor == superuser
        assert event.tenant == tenant
        assert event.entity_type == "Store"
        assert event.entity_id == response.data["id"]
        assert "ip" in event.metadata
        assert "user_agent" in event.metadata
        assert "endpoint" in event.metadata
        assert "method" in event.metadata

    def test_store_create_audit_scoped_to_correct_store(
        self, api_client, regular_user, tenant, company, all_permissions
    ):
        """Audit records the scope headers that were active during the request."""
        Membership.objects.create(user=regular_user, tenant=tenant, company=company)
        _setup_role_binding(regular_user, tenant, ["stores:write", "stores:read"])

        api_client.force_authenticate(user=regular_user)
        url = reverse("stores-list")

        response = api_client.post(
            url,
            {"company": str(company.id), "name": "Loja Norte", "slug": "norte"},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_201_CREATED

        event = AuditEvent.objects.get(action="store:create")
        assert event.tenant == tenant


@pytest.mark.django_db
class TestAuditOnCompanyCreate:
    def test_company_create_generates_audit_event(self, api_client, superuser, tenant):
        api_client.force_authenticate(user=superuser)
        url = reverse("companies-list")
        response = api_client.post(
            url,
            {"tenant": str(tenant.id), "name": "New Co", "slug": "new-co"},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert AuditEvent.objects.filter(action="company:create").count() == 1


@pytest.mark.django_db
class TestAuditOnRoleCreate:
    def test_role_create_generates_audit_event(self, api_client, superuser, tenant, all_permissions):
        api_client.force_authenticate(user=superuser)
        url = reverse("roles-list")
        perm = Permission.objects.get(codename="stores:read")
        response = api_client.post(
            url,
            {"name": "Store Viewer", "tenant": str(tenant.id), "permissions": [str(perm.id)]},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert AuditEvent.objects.filter(action="role:create").count() == 1


@pytest.mark.django_db
class TestAuditOnUserCreate:
    def test_user_create_generates_audit_event(self, api_client, superuser, tenant, all_permissions):
        api_client.force_authenticate(user=superuser)
        url = reverse("users-list")
        response = api_client.post(
            url,
            {"email": "new@example.com", "name": "New User", "password": "strong1234"},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert AuditEvent.objects.filter(action="user:create").count() == 1


@pytest.mark.django_db
class TestAuditOnMembershipCreate:
    def test_membership_create_generates_audit_event(
        self, api_client, superuser, tenant, regular_user, all_permissions
    ):
        api_client.force_authenticate(user=superuser)
        url = reverse("memberships-list")
        response = api_client.post(
            url,
            {"user": str(regular_user.id), "tenant": str(tenant.id)},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert AuditEvent.objects.filter(action="membership:create").count() == 1


@pytest.mark.django_db
class TestAuditOnRoleBindingCreate:
    def test_rolebinding_create_generates_audit_event(
        self, api_client, superuser, tenant, regular_user, all_permissions
    ):
        role = Role.objects.create(name="Admin", tenant=tenant)
        role.permissions.add(*Permission.objects.all())

        api_client.force_authenticate(user=superuser)
        url = reverse("role-bindings-list")
        response = api_client.post(
            url,
            {"user": str(regular_user.id), "role": str(role.id), "tenant": str(tenant.id)},
            format="json",
            HTTP_X_TENANT_ID=str(tenant.id),
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert AuditEvent.objects.filter(action="rolebinding:create").count() == 1


@pytest.mark.django_db
class TestAuditListEndpoint:
    def test_superuser_can_list_audit_events(self, api_client, superuser, tenant, company):
        AuditEvent.objects.create(
            actor=superuser, tenant=tenant, action="company:create",
            entity_type="Company", entity_id=str(company.id),
        )
        api_client.force_authenticate(user=superuser)
        url = reverse("audit-list")
        response = api_client.get(url, HTTP_X_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_audit_filter_by_tenant(self, api_client, superuser, tenant):
        other_tenant = Tenant.objects.create(name="Other", slug="other")
        AuditEvent.objects.create(actor=superuser, tenant=tenant, action="test:a", entity_type="Test", entity_id="1")
        AuditEvent.objects.create(
            actor=superuser, tenant=other_tenant, action="test:b", entity_type="Test", entity_id="2"
        )

        api_client.force_authenticate(user=superuser)
        url = reverse("audit-list")
        response = api_client.get(url, HTTP_X_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["action"] == "test:a"
