"""Tests for the health check endpoint."""

import pytest
from django.test import Client


@pytest.mark.django_db
def test_health_returns_200():
    client = Client()
    response = client.get("/health/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_health_returns_status_ok():
    client = Client()
    response = client.get("/health/")
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_health_rejects_post():
    client = Client()
    response = client.post("/health/")
    assert response.status_code == 405
