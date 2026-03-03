import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tenants.models import User


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
