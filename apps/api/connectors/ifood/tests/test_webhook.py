import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import pytest
from django.test import Client

SECRET = "test-secret"

SAMPLE_EVENT = {
    "id": "evt-abc-123",
    "code": "PLACED",
    "orderId": "order-xyz-456",
    "merchantId": "merchant-001",
}


def sign(payload_bytes: bytes) -> str:
    return hmac.new(SECRET.encode(), payload_bytes, hashlib.sha256).hexdigest()


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
def test_webhook_returns_202_with_valid_signature(client, settings):
    settings.IFOOD_WEBHOOK_SECRET = SECRET
    payload = json.dumps(SAMPLE_EVENT).encode()

    with patch("connectors.ifood.views.process_ifood_event") as mock_task:
        mock_task.delay = MagicMock()
        response = client.post(
            "/api/v1/webhooks/ifood/",
            data=payload,
            content_type="application/json",
            HTTP_X_IFOOD_SIGNATURE=sign(payload),
        )

    assert response.status_code == 202
    assert response.json()["received"] is True


@pytest.mark.django_db
def test_webhook_returns_401_with_invalid_signature(client, settings):
    settings.IFOOD_WEBHOOK_SECRET = SECRET
    payload = json.dumps(SAMPLE_EVENT).encode()

    response = client.post(
        "/api/v1/webhooks/ifood/",
        data=payload,
        content_type="application/json",
        HTTP_X_IFOOD_SIGNATURE="invalid-signature",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_webhook_persists_raw_event(client, settings):
    from connectors.ifood.models import RawEvent

    settings.IFOOD_WEBHOOK_SECRET = SECRET
    payload = json.dumps(SAMPLE_EVENT).encode()

    with patch("connectors.ifood.views.process_ifood_event") as mock_task:
        mock_task.delay = MagicMock()
        client.post(
            "/api/v1/webhooks/ifood/",
            data=payload,
            content_type="application/json",
            HTTP_X_IFOOD_SIGNATURE=sign(payload),
        )

    assert RawEvent.objects.filter(event_id="evt-abc-123").exists()


@pytest.mark.django_db
def test_webhook_enqueues_task(client, settings):
    settings.IFOOD_WEBHOOK_SECRET = SECRET
    payload = json.dumps(SAMPLE_EVENT).encode()

    with patch("connectors.ifood.views.process_ifood_event") as mock_task:
        mock_task.delay = MagicMock()
        client.post(
            "/api/v1/webhooks/ifood/",
            data=payload,
            content_type="application/json",
            HTTP_X_IFOOD_SIGNATURE=sign(payload),
        )

    mock_task.delay.assert_called_once()


@pytest.mark.django_db
def test_webhook_invalid_json_returns_400(client, settings):
    settings.IFOOD_WEBHOOK_SECRET = SECRET
    payload = b"not-json"

    response = client.post(
        "/api/v1/webhooks/ifood/",
        data=payload,
        content_type="application/json",
        HTTP_X_IFOOD_SIGNATURE=sign(payload),
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_webhook_raw_event_status_is_enqueued(client, settings):
    """After successful webhook, RawEvent status should be ENQUEUED."""
    from connectors.ifood.models import RawEvent, RawEventStatus

    settings.IFOOD_WEBHOOK_SECRET = SECRET
    payload = json.dumps(SAMPLE_EVENT).encode()

    with patch("connectors.ifood.views.process_ifood_event") as mock_task:
        mock_task.delay = MagicMock()
        client.post(
            "/api/v1/webhooks/ifood/",
            data=payload,
            content_type="application/json",
            HTTP_X_IFOOD_SIGNATURE=sign(payload),
        )

    raw_event = RawEvent.objects.get(event_id="evt-abc-123")
    assert raw_event.status == RawEventStatus.ENQUEUED


@pytest.mark.django_db
def test_webhook_rejects_get(client):
    response = client.get("/api/v1/webhooks/ifood/")
    assert response.status_code == 405
