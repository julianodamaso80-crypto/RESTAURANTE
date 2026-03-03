from unittest.mock import MagicMock, patch

import pytest

from connectors.ninetynine.client import NinetyNineAPIClient, NinetyNineOrderNotFoundError


def make_client():
    return NinetyNineAPIClient(access_token="fake-token-99")


def test_get_order_success():
    client = make_client()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "order-99-1", "items": []}
    with patch.object(client.session, "get", return_value=mock_resp):
        result = client.get_order("order-99-1")
    assert result["id"] == "order-99-1"


def test_get_order_404_retries_and_raises():
    client = make_client()
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    with patch.object(client.session, "get", return_value=mock_resp):
        with patch("connectors.ninetynine.client.time.sleep"):
            with pytest.raises(NinetyNineOrderNotFoundError):
                client.get_order("missing", max_retries=2, base_delay=0.01)


def test_exponential_backoff():
    client = make_client()
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    sleep_calls = []
    with patch.object(client.session, "get", return_value=mock_resp):
        with patch("connectors.ninetynine.client.time.sleep", side_effect=lambda d: sleep_calls.append(d)):
            with pytest.raises(NinetyNineOrderNotFoundError):
                client.get_order("order-x", max_retries=3, base_delay=1.0)
    assert sleep_calls == [1.0, 2.0, 4.0]


def test_404_then_200_succeeds():
    client = make_client()
    resp_404 = MagicMock()
    resp_404.status_code = 404
    resp_200 = MagicMock()
    resp_200.status_code = 200
    resp_200.json.return_value = {"id": "order-99-1"}
    with patch.object(client.session, "get", side_effect=[resp_404, resp_200]):
        with patch("connectors.ninetynine.client.time.sleep"):
            result = client.get_order("order-99-1", max_retries=2, base_delay=0.01)
    assert result["id"] == "order-99-1"
