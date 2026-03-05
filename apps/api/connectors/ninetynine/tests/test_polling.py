from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from connectors.ifood.models import RawEvent
from connectors.ninetynine.models import NinetyNineStoreCredential
from connectors.ninetynine.polling import poll_ninetynine_store


def _create_cred(store):
    return NinetyNineStoreCredential.objects.create(
        store=store,
        merchant_id="merchant-99-001",
        client_id="APP-SHOP-12345",
        client_secret="APP-SHOP-12345",
        access_token="token-valid",
        is_active=True,
        token_expires_at=timezone.now() + timedelta(hours=5),
    )


@pytest.mark.django_db
def test_polling_no_events_schedules_next(store_factory):
    store = store_factory()
    # store_factory already creates a credential, get it
    cred = NinetyNineStoreCredential.objects.get(store=store)
    cred.token_expires_at = timezone.now() + timedelta(hours=5)
    cred.save(update_fields=["token_expires_at"])

    mock_response = MagicMock()
    mock_response.status_code = 204

    with patch("connectors.ninetynine.polling.requests.get", return_value=mock_response):
        with patch("connectors.ninetynine.polling.poll_ninetynine_store.apply_async") as mock_async:
            poll_ninetynine_store(str(store.id))

    mock_async.assert_called_once_with(args=[str(store.id)], countdown=30)


@pytest.mark.django_db
def test_polling_creates_raw_event(store_factory):
    store = store_factory()
    cred = NinetyNineStoreCredential.objects.get(store=store)
    cred.token_expires_at = timezone.now() + timedelta(hours=5)
    cred.save(update_fields=["token_expires_at"])

    mock_get = MagicMock()
    mock_get.status_code = 200
    mock_get.json.return_value = [
        {"id": "evt-99-poll-001", "code": "PLACED", "orderId": "order-99-001"}
    ]

    mock_post = MagicMock()
    mock_post.status_code = 202

    with patch("connectors.ninetynine.polling.requests.get", return_value=mock_get):
        with patch("connectors.ninetynine.polling.requests.post", return_value=mock_post):
            with patch("connectors.ninetynine.tasks.process_ninetynine_event") as mock_task:
                mock_task.delay = MagicMock()
                with patch("connectors.ninetynine.polling.poll_ninetynine_store.apply_async"):
                    poll_ninetynine_store(str(store.id))

    assert RawEvent.objects.filter(event_id="evt-99-poll-001", source="99food").exists()
    mock_task.delay.assert_called_once()


@pytest.mark.django_db
def test_polling_deduplicates_events(store_factory):
    store = store_factory()
    cred = NinetyNineStoreCredential.objects.get(store=store)
    cred.token_expires_at = timezone.now() + timedelta(hours=5)
    cred.save(update_fields=["token_expires_at"])

    # Pre-create an event so it's a duplicate
    RawEvent.objects.create(
        source="99food",
        event_id="evt-99-dup-001",
        event_type="PLACED",
        payload={},
    )

    mock_get = MagicMock()
    mock_get.status_code = 200
    mock_get.json.return_value = [
        {"id": "evt-99-dup-001", "code": "PLACED", "orderId": "order-99-001"}
    ]

    mock_post = MagicMock()
    mock_post.status_code = 202

    with patch("connectors.ninetynine.polling.requests.get", return_value=mock_get):
        with patch("connectors.ninetynine.polling.requests.post", return_value=mock_post):
            with patch("connectors.ninetynine.tasks.process_ninetynine_event") as mock_task:
                mock_task.delay = MagicMock()
                with patch("connectors.ninetynine.polling.poll_ninetynine_store.apply_async"):
                    poll_ninetynine_store(str(store.id))

    # Should NOT have created a new RawEvent or called process
    assert RawEvent.objects.filter(event_id="evt-99-dup-001", source="99food").count() == 1
    mock_task.delay.assert_not_called()


@pytest.mark.django_db
def test_polling_store_not_found_returns_early():
    with patch("connectors.ninetynine.polling.poll_ninetynine_store.apply_async") as mock_async:
        poll_ninetynine_store("00000000-0000-0000-0000-000000000000")

    mock_async.assert_not_called()


@pytest.mark.django_db
def test_polling_refreshes_expiring_token(store_factory):
    store = store_factory()
    cred = NinetyNineStoreCredential.objects.get(store=store)
    # Token expires in 10 minutes — should trigger refresh
    cred.token_expires_at = timezone.now() + timedelta(minutes=10)
    cred.save(update_fields=["token_expires_at"])

    mock_response = MagicMock()
    mock_response.status_code = 204

    with patch("connectors.ninetynine.oauth.NinetyNineAuthClient") as MockAuth:
        mock_auth_instance = MockAuth.return_value
        mock_auth_instance.get_token.return_value = {
            "access_token": "new-refreshed-token",
            "expires_in": 21600,
        }

        with patch("connectors.ninetynine.polling.requests.get", return_value=mock_response):
            with patch("connectors.ninetynine.polling.poll_ninetynine_store.apply_async"):
                poll_ninetynine_store(str(store.id))

    cred.refresh_from_db()
    assert cred.access_token == "new-refreshed-token"


@pytest.mark.django_db
def test_polling_401_retries_with_new_token(store_factory):
    store = store_factory()
    cred = NinetyNineStoreCredential.objects.get(store=store)
    cred.token_expires_at = timezone.now() + timedelta(hours=5)
    cred.save(update_fields=["token_expires_at"])

    mock_response = MagicMock()
    mock_response.status_code = 401

    with patch("connectors.ninetynine.oauth.NinetyNineAuthClient") as MockAuth:
        mock_auth_instance = MockAuth.return_value
        mock_auth_instance.get_token.return_value = {
            "access_token": "new-token-after-401",
        }

        with patch("connectors.ninetynine.polling.requests.get", return_value=mock_response):
            with patch("connectors.ninetynine.polling.poll_ninetynine_store.apply_async") as mock_async:
                poll_ninetynine_store(str(store.id))

    # Schedules retry with short countdown
    mock_async.assert_called_once_with(args=[str(store.id)], countdown=5)


@pytest.mark.django_db
def test_polling_network_error_schedules_retry(store_factory):
    import requests as req

    store = store_factory()
    cred = NinetyNineStoreCredential.objects.get(store=store)
    cred.token_expires_at = timezone.now() + timedelta(hours=5)
    cred.save(update_fields=["token_expires_at"])

    with patch(
        "connectors.ninetynine.polling.requests.get",
        side_effect=req.RequestException("timeout"),
    ):
        with patch("connectors.ninetynine.polling.poll_ninetynine_store.apply_async") as mock_async:
            poll_ninetynine_store(str(store.id))

    mock_async.assert_called_once_with(args=[str(store.id)], countdown=60)
