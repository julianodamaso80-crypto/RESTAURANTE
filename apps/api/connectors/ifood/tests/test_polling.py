"""Tests for iFood order polling task."""

from unittest.mock import MagicMock, patch

import pytest
import requests as req

from connectors.ifood.client import IFoodAPIClient, IFoodAPIError
from connectors.ifood.models import RawEvent, RawEventStatus

SAMPLE_EVENTS = [
    {
        "id": "evt-poll-001",
        "code": "PLACED",
        "orderId": "order-aaa",
        "merchantId": "merchant-0001",
        "createdAt": "2026-03-03T10:00:00Z",
    },
    {
        "id": "evt-poll-002",
        "code": "CONFIRMED",
        "orderId": "order-bbb",
        "merchantId": "merchant-0001",
        "createdAt": "2026-03-03T10:00:01Z",
    },
]


# ---------------------------------------------------------------------------
# Client: poll_events
# ---------------------------------------------------------------------------


class TestPollEventsClient:
    def test_poll_events_success(self):
        client = IFoodAPIClient(access_token="fake-token")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = SAMPLE_EVENTS

        with patch.object(client.session, "get", return_value=mock_resp):
            result = client.poll_events(merchant_id="merchant-001")

        assert len(result) == 2
        assert result[0]["id"] == "evt-poll-001"

    def test_poll_events_204_no_content(self):
        client = IFoodAPIClient(access_token="fake-token")
        mock_resp = MagicMock()
        mock_resp.status_code = 204

        with patch.object(client.session, "get", return_value=mock_resp):
            result = client.poll_events(merchant_id="merchant-001")

        assert result == []

    def test_poll_events_401_raises(self):
        client = IFoodAPIClient(access_token="expired-token")
        mock_resp = MagicMock()
        mock_resp.status_code = 401

        with patch.object(client.session, "get", return_value=mock_resp):
            with pytest.raises(IFoodAPIError, match="Unauthorized"):
                client.poll_events(merchant_id="merchant-001")

    def test_poll_events_network_error_returns_empty(self):
        client = IFoodAPIClient(access_token="fake-token")

        with patch.object(client.session, "get", side_effect=req.Timeout("timeout")):
            result = client.poll_events(merchant_id="merchant-001")

        assert result == []

    def test_poll_events_500_returns_empty(self):
        client = IFoodAPIClient(access_token="fake-token")
        mock_resp = MagicMock()
        mock_resp.status_code = 500

        with patch.object(client.session, "get", return_value=mock_resp):
            result = client.poll_events(merchant_id="merchant-001")

        assert result == []


# ---------------------------------------------------------------------------
# Client: acknowledge_events
# ---------------------------------------------------------------------------


class TestAcknowledgeEventsClient:
    def test_acknowledge_success(self):
        client = IFoodAPIClient(access_token="fake-token")
        mock_resp = MagicMock()
        mock_resp.status_code = 202

        with patch.object(client.session, "post", return_value=mock_resp) as mock_post:
            result = client.acknowledge_events(["evt-1", "evt-2"])

        assert result is True
        posted_payload = mock_post.call_args[1]["json"]
        assert posted_payload == [{"id": "evt-1"}, {"id": "evt-2"}]

    def test_acknowledge_empty_list_returns_true(self):
        client = IFoodAPIClient(access_token="fake-token")
        result = client.acknowledge_events([])
        assert result is True

    def test_acknowledge_network_error_returns_false(self):
        client = IFoodAPIClient(access_token="fake-token")

        with patch.object(client.session, "post", side_effect=req.ConnectionError("fail")):
            result = client.acknowledge_events(["evt-1"])

        assert result is False


# ---------------------------------------------------------------------------
# Task: poll_ifood_orders
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPollIfoodOrdersTask:
    def test_poll_creates_raw_events_and_enqueues(self, store_factory):
        """Happy path: 2 events polled -> 2 RawEvents -> 2 tasks enqueued -> acked."""
        store_factory()

        with (
            patch("connectors.ifood.polling.IFoodAPIClient") as MockClient,
            patch("connectors.ifood.tasks.process_ifood_event") as mock_task,
        ):
            mock_instance = MockClient.return_value
            mock_instance.poll_events.return_value = SAMPLE_EVENTS
            mock_instance.acknowledge_events.return_value = True
            mock_task.delay = MagicMock()

            from connectors.ifood.polling import poll_ifood_orders

            result = poll_ifood_orders()

        assert result["stores_polled"] == 1
        assert result["new_events"] == 2
        assert RawEvent.objects.filter(source="ifood", event_id="evt-poll-001").exists()
        assert RawEvent.objects.filter(source="ifood", event_id="evt-poll-002").exists()
        assert mock_task.delay.call_count == 2
        mock_instance.acknowledge_events.assert_called_once_with(["evt-poll-001", "evt-poll-002"])

    def test_poll_empty_response(self, store_factory):
        """No events -> no RawEvents, no tasks."""
        store_factory()

        with (
            patch("connectors.ifood.polling.IFoodAPIClient") as MockClient,
            patch("connectors.ifood.tasks.process_ifood_event") as mock_task,
        ):
            mock_instance = MockClient.return_value
            mock_instance.poll_events.return_value = []
            mock_task.delay = MagicMock()

            from connectors.ifood.polling import poll_ifood_orders

            result = poll_ifood_orders()

        assert result["new_events"] == 0
        assert mock_task.delay.call_count == 0

    def test_poll_skips_duplicate_events(self, store_factory, raw_event_factory):
        """Event already exists -> skip, but still ack with iFood."""
        store_factory()
        raw_event_factory(event_id="evt-poll-001", source="ifood")

        with (
            patch("connectors.ifood.polling.IFoodAPIClient") as MockClient,
            patch("connectors.ifood.tasks.process_ifood_event") as mock_task,
        ):
            mock_instance = MockClient.return_value
            mock_instance.poll_events.return_value = [SAMPLE_EVENTS[0]]
            mock_instance.acknowledge_events.return_value = True
            mock_task.delay = MagicMock()

            from connectors.ifood.polling import poll_ifood_orders

            result = poll_ifood_orders()

        assert result["new_events"] == 0
        assert mock_task.delay.call_count == 0
        mock_instance.acknowledge_events.assert_called_once_with(["evt-poll-001"])

    def test_poll_one_store_fails_others_continue(self, store_factory):
        """Store A raises -> Store B still polled."""
        store_factory()
        store_factory()

        call_count = {"n": 0}

        def mock_poll_events(merchant_id):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise Exception("Simulated API failure")
            return [SAMPLE_EVENTS[0]]

        with (
            patch("connectors.ifood.polling.IFoodAPIClient") as MockClient,
            patch("connectors.ifood.tasks.process_ifood_event") as mock_task,
        ):
            mock_instance = MockClient.return_value
            mock_instance.poll_events.side_effect = mock_poll_events
            mock_instance.acknowledge_events.return_value = True
            mock_task.delay = MagicMock()

            from connectors.ifood.polling import poll_ifood_orders

            result = poll_ifood_orders()

        assert result["stores_polled"] == 1
        assert result["new_events"] == 1

    def test_poll_skips_credentials_without_token(self, db):
        """Credentials with empty access_token are excluded."""
        from connectors.ifood.tests.factories import IFoodStoreCredentialFactory

        IFoodStoreCredentialFactory(access_token="", is_active=True)

        with (
            patch("connectors.ifood.polling.IFoodAPIClient") as MockClient,
            patch("connectors.ifood.tasks.process_ifood_event"),
        ):
            from connectors.ifood.polling import poll_ifood_orders

            result = poll_ifood_orders()

        assert result["stores_polled"] == 0
        MockClient.assert_not_called()

    def test_poll_skips_inactive_credentials(self, db):
        """Inactive credentials are not polled."""
        from connectors.ifood.tests.factories import IFoodStoreCredentialFactory

        IFoodStoreCredentialFactory(is_active=False, access_token="valid-token")

        with (
            patch("connectors.ifood.polling.IFoodAPIClient"),
            patch("connectors.ifood.tasks.process_ifood_event"),
        ):
            from connectors.ifood.polling import poll_ifood_orders

            result = poll_ifood_orders()

        assert result["stores_polled"] == 0

    def test_raw_event_status_is_enqueued(self, store_factory):
        """Polled RawEvent should end in ENQUEUED status with polling header."""
        store_factory()

        with (
            patch("connectors.ifood.polling.IFoodAPIClient") as MockClient,
            patch("connectors.ifood.tasks.process_ifood_event") as mock_task,
        ):
            mock_instance = MockClient.return_value
            mock_instance.poll_events.return_value = [SAMPLE_EVENTS[0]]
            mock_instance.acknowledge_events.return_value = True
            mock_task.delay = MagicMock()

            from connectors.ifood.polling import poll_ifood_orders

            poll_ifood_orders()

        raw_event = RawEvent.objects.get(event_id="evt-poll-001")
        assert raw_event.status == RawEventStatus.ENQUEUED
        assert raw_event.headers == {"ingestion": "polling"}

    def test_raw_event_has_tenant_and_store(self, store_factory):
        """Polled RawEvent should have tenant_id and store_id from the credential."""
        store = store_factory()

        with (
            patch("connectors.ifood.polling.IFoodAPIClient") as MockClient,
            patch("connectors.ifood.tasks.process_ifood_event") as mock_task,
        ):
            mock_instance = MockClient.return_value
            mock_instance.poll_events.return_value = [SAMPLE_EVENTS[0]]
            mock_instance.acknowledge_events.return_value = True
            mock_task.delay = MagicMock()

            from connectors.ifood.polling import poll_ifood_orders

            poll_ifood_orders()

        raw_event = RawEvent.objects.get(event_id="evt-poll-001")
        assert raw_event.tenant_id == store.company.tenant.id
        assert raw_event.store_id == store.id
