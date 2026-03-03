import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import pytest

SECRET = "test-99food-secret"


def sign(payload_bytes: bytes) -> str:
    return hmac.new(SECRET.encode(), payload_bytes, hashlib.sha256).hexdigest()


SAMPLE_EVENT = {
    "id": "evt-99-abc",
    "code": "PLACED",
    "orderId": "order-99-xyz",
    "merchantId": "merchant-99-001",
}


@pytest.mark.django_db
def test_webhook_returns_202_valid_signature(client, settings):
    settings.NINETYNINE_WEBHOOK_SECRET = SECRET
    payload = json.dumps(SAMPLE_EVENT).encode()

    with patch("connectors.ninetynine.views.process_ninetynine_event") as mock_task:
        mock_task.delay = MagicMock()
        response = client.post(
            "/api/v1/webhooks/99food/",
            data=payload,
            content_type="application/json",
            HTTP_X_NINETYNINE_SIGNATURE=sign(payload),
        )

    assert response.status_code == 202
    assert response.json()["received"] is True


@pytest.mark.django_db
def test_webhook_returns_401_invalid_signature(client, settings):
    settings.NINETYNINE_WEBHOOK_SECRET = SECRET
    payload = json.dumps(SAMPLE_EVENT).encode()
    response = client.post(
        "/api/v1/webhooks/99food/",
        data=payload,
        content_type="application/json",
        HTTP_X_NINETYNINE_SIGNATURE="assinatura-errada",
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_webhook_persists_raw_event_with_source_99food(client, settings):
    from connectors.ifood.models import RawEvent

    settings.NINETYNINE_WEBHOOK_SECRET = SECRET
    payload = json.dumps(SAMPLE_EVENT).encode()

    with patch("connectors.ninetynine.views.process_ninetynine_event") as mock_task:
        mock_task.delay = MagicMock()
        client.post(
            "/api/v1/webhooks/99food/",
            data=payload,
            content_type="application/json",
            HTTP_X_NINETYNINE_SIGNATURE=sign(payload),
        )

    assert RawEvent.objects.filter(event_id="evt-99-abc", source="99food").exists()


@pytest.mark.django_db
def test_webhook_enqueues_celery_task(client, settings):
    settings.NINETYNINE_WEBHOOK_SECRET = SECRET
    payload = json.dumps(SAMPLE_EVENT).encode()

    with patch("connectors.ninetynine.views.process_ninetynine_event") as mock_task:
        mock_task.delay = MagicMock()
        client.post(
            "/api/v1/webhooks/99food/",
            data=payload,
            content_type="application/json",
            HTTP_X_NINETYNINE_SIGNATURE=sign(payload),
        )

    mock_task.delay.assert_called_once()


@pytest.mark.django_db
def test_webhook_invalid_json_returns_400(client, settings):
    settings.NINETYNINE_WEBHOOK_SECRET = SECRET
    payload = b"not-json-at-all"
    response = client.post(
        "/api/v1/webhooks/99food/",
        data=payload,
        content_type="application/json",
        HTTP_X_NINETYNINE_SIGNATURE=sign(payload),
    )
    assert response.status_code == 400
