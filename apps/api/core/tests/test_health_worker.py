from unittest.mock import patch

import pytest


@pytest.mark.django_db
def test_health_worker_returns_503_when_no_workers(client):
    with patch("core.views.Control") as mock_control:
        mock_control.return_value.ping.return_value = []
        response = client.get("/api/v1/health/worker/")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"


@pytest.mark.django_db
def test_health_worker_returns_200_when_workers_up(client):
    with patch("core.views.Control") as mock_control:
        mock_control.return_value.ping.return_value = [{"worker1": {"ok": "pong"}}]
        response = client.get("/api/v1/health/worker/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["workers"] == 1


@pytest.mark.django_db
def test_health_worker_returns_503_on_exception(client):
    with patch("core.views.Control") as mock_control:
        mock_control.return_value.ping.side_effect = Exception("broker down")
        response = client.get("/api/v1/health/worker/")
    assert response.status_code == 503
    assert response.json()["status"] == "error"
