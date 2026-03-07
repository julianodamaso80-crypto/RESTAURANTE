import json
from unittest.mock import MagicMock, patch

import pytest

SECRET = "test-rappi-secret"

SAMPLE_EVENT = {
    "id": "evt-rappi-abc",
    "event": "NEW_ORDER",
    "orderId": "order-rappi-xyz",
    "store_id": "rappi-store-001",
}


@pytest.mark.django_db
def test_webhook_returns_202_valid_secret(client, settings):
    settings.RAPPI_WEBHOOK_SECRET = SECRET
    payload = json.dumps(SAMPLE_EVENT).encode()

    with patch("connectors.rappi.views.process_rappi_event") as mock_task:
        mock_task.delay = MagicMock()
        response = client.post(
            "/api/v1/connect/rappi/webhook/",
            data=payload,
            content_type="application/json",
            HTTP_X_RAPPI_SECRET=SECRET,
        )

    assert response.status_code == 202
    assert response.json()["received"] is True


@pytest.mark.django_db
def test_webhook_returns_401_invalid_secret(client, settings):
    settings.RAPPI_WEBHOOK_SECRET = SECRET
    payload = json.dumps(SAMPLE_EVENT).encode()
    response = client.post(
        "/api/v1/connect/rappi/webhook/",
        data=payload,
        content_type="application/json",
        HTTP_X_RAPPI_SECRET="wrong-secret",
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_webhook_allows_no_secret_when_unconfigured(client, settings):
    settings.RAPPI_WEBHOOK_SECRET = ""
    payload = json.dumps(SAMPLE_EVENT).encode()

    with patch("connectors.rappi.views.process_rappi_event") as mock_task:
        mock_task.delay = MagicMock()
        response = client.post(
            "/api/v1/connect/rappi/webhook/",
            data=payload,
            content_type="application/json",
        )

    assert response.status_code == 202


@pytest.mark.django_db
def test_webhook_persists_raw_event_with_source_rappi(client, settings):
    from connectors.ifood.models import RawEvent

    settings.RAPPI_WEBHOOK_SECRET = ""
    payload = json.dumps(SAMPLE_EVENT).encode()

    with patch("connectors.rappi.views.process_rappi_event") as mock_task:
        mock_task.delay = MagicMock()
        client.post(
            "/api/v1/connect/rappi/webhook/",
            data=payload,
            content_type="application/json",
        )

    assert RawEvent.objects.filter(event_id="evt-rappi-abc", source="rappi").exists()


@pytest.mark.django_db
def test_webhook_enqueues_celery_task(client, settings):
    settings.RAPPI_WEBHOOK_SECRET = ""
    payload = json.dumps(SAMPLE_EVENT).encode()

    with patch("connectors.rappi.views.process_rappi_event") as mock_task:
        mock_task.delay = MagicMock()
        client.post(
            "/api/v1/connect/rappi/webhook/",
            data=payload,
            content_type="application/json",
        )

    mock_task.delay.assert_called_once()


@pytest.mark.django_db
def test_webhook_invalid_json_returns_400(client, settings):
    settings.RAPPI_WEBHOOK_SECRET = ""
    payload = b"not-json-at-all"
    response = client.post(
        "/api/v1/connect/rappi/webhook/",
        data=payload,
        content_type="application/json",
    )
    assert response.status_code == 400
