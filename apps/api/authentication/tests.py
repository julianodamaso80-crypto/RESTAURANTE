import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tenants.models import Membership, Tenant, User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="user@example.com", password="testpass123", name="Test User")


@pytest.mark.django_db
class TestJWTLogin:
    def test_login_returns_tokens(self, api_client, user):
        url = reverse("token_obtain_pair")
        response = api_client.post(url, {"email": "user@example.com", "password": "testpass123"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_wrong_password_returns_401(self, api_client, user):
        url = reverse("token_obtain_pair")
        response = api_client.post(url, {"email": "user@example.com", "password": "wrong"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user_returns_401(self, api_client, db):
        url = reverse("token_obtain_pair")
        response = api_client.post(url, {"email": "noone@example.com", "password": "testpass123"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestJWTRefresh:
    def test_refresh_returns_new_access_token(self, api_client, user):
        login_url = reverse("token_obtain_pair")
        response = api_client.post(login_url, {"email": "user@example.com", "password": "testpass123"}, format="json")
        refresh_token = response.data["refresh"]

        refresh_url = reverse("token_refresh")
        response = api_client.post(refresh_url, {"refresh": refresh_token}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_refresh_invalid_token_returns_401(self, api_client, db):
        refresh_url = reverse("token_refresh")
        response = api_client.post(refresh_url, {"refresh": "invalid-token"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestRegister:
    def test_register_creates_user_and_returns_tokens(self, api_client):
        url = reverse("register")
        response = api_client.post(
            url,
            {
                "nome_completo": "Maria Silva",
                "email": "maria@bomsabor.com.br",
                "senha": "minha-senha-123",
                "nome_restaurante": "Bom Sabor",
                "telefone": "11999999999",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["user"]["email"] == "maria@bomsabor.com.br"
        assert response.data["user"]["full_name"] == "Maria Silva"
        assert response.data["tenant_id"]
        assert response.data["store_id"]

        # Verify DB objects were created
        assert User.objects.filter(email="maria@bomsabor.com.br").exists()
        assert Tenant.objects.filter(name="Bom Sabor").exists()
        assert Membership.objects.filter(user__email="maria@bomsabor.com.br").exists()

    def test_register_duplicate_email_returns_400(self, api_client):
        User.objects.create_user(email="dup@test.com", password="pass123", name="Dup")
        url = reverse("register")
        response = api_client.post(
            url,
            {
                "nome_completo": "Outro",
                "email": "dup@test.com",
                "senha": "pass-456",
                "nome_restaurante": "Outro Restaurante",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_msg = response.data.get("error", "").lower()
        assert "email" in error_msg or "cadastrado" in error_msg

    def test_register_missing_fields_returns_400(self, api_client):
        url = reverse("register")
        response = api_client.post(url, {"email": "only@email.com"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_short_password_returns_400(self, api_client):
        url = reverse("register")
        response = api_client.post(
            url,
            {
                "nome_completo": "Test",
                "email": "test@test.com",
                "senha": "123",
                "nome_restaurante": "Test",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
