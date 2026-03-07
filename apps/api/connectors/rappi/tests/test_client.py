from unittest.mock import MagicMock, patch

import pytest

from connectors.rappi.client import RappiAPIClient, RappiOrderNotFoundError


def make_client():
    return RappiAPIClient(rappi_token="fake-token-rappi")


def test_get_order_success():
    client = make_client()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "order-rappi-1", "items": []}
    with patch.object(client.session, "get", return_value=mock_resp):
        result = client.get_order("order-rappi-1")
    assert result["id"] == "order-rappi-1"


def test_get_order_404_retries_and_raises():
    client = make_client()
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    with patch.object(client.session, "get", return_value=mock_resp):
        with patch("connectors.rappi.client.time.sleep"):
            with pytest.raises(RappiOrderNotFoundError):
                client.get_order("missing", max_retries=2, base_delay=0.01)


def test_exponential_backoff():
    client = make_client()
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    sleep_calls = []
    with patch.object(client.session, "get", return_value=mock_resp):
        with patch("connectors.rappi.client.time.sleep", side_effect=lambda d: sleep_calls.append(d)):
            with pytest.raises(RappiOrderNotFoundError):
                client.get_order("order-x", max_retries=3, base_delay=1.0)
    assert sleep_calls == [1.0, 2.0, 4.0]


def test_stub_mode_get_order():
    with patch("connectors.rappi.client.RAPPI_STUB_MODE", True):
        client = make_client()
        result = client.get_order("any-order-id")
    assert result["id"] == "any-order-id"
    assert "items" in result


def test_stub_mode_check_connection():
    with patch("connectors.rappi.client.RAPPI_STUB_MODE", True):
        client = make_client()
        assert client.check_connection() is True


def test_auth_header_format():
    client = make_client()
    assert client.session.headers["x-authorization"] == "Bearer fake-token-rappi"
