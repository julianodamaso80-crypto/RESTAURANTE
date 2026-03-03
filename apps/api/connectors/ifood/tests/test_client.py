from unittest.mock import MagicMock, patch

import pytest

from connectors.ifood.client import IFoodAPIClient, IFoodAPIError, IFoodOrderNotFoundError


def make_client():
    return IFoodAPIClient(access_token="fake-token")


def test_get_order_success():
    client = make_client()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "order-1", "items": []}

    with patch.object(client.session, "get", return_value=mock_response):
        result = client.get_order("order-1")

    assert result["id"] == "order-1"


def test_get_order_404_retries_and_raises():
    client = make_client()
    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch.object(client.session, "get", return_value=mock_response):
        with patch("connectors.ifood.client.time.sleep"):
            with pytest.raises(IFoodOrderNotFoundError):
                client.get_order("order-missing", max_retries=2, base_delay=0.01)


def test_get_order_404_then_200_succeeds():
    client = make_client()

    resp_404 = MagicMock()
    resp_404.status_code = 404
    resp_200 = MagicMock()
    resp_200.status_code = 200
    resp_200.json.return_value = {"id": "order-1"}

    with patch.object(client.session, "get", side_effect=[resp_404, resp_200]):
        with patch("connectors.ifood.client.time.sleep"):
            result = client.get_order("order-1", max_retries=2, base_delay=0.01)

    assert result["id"] == "order-1"


def test_get_order_uses_exponential_backoff():
    client = make_client()
    resp_404 = MagicMock()
    resp_404.status_code = 404

    sleep_calls = []

    with patch.object(client.session, "get", return_value=resp_404):
        with patch("connectors.ifood.client.time.sleep", side_effect=lambda d: sleep_calls.append(d)):
            with pytest.raises(IFoodOrderNotFoundError):
                client.get_order("order-x", max_retries=3, base_delay=1.0)

    # Should call sleep with 1, 2, 4 (exponential)
    assert sleep_calls == [1.0, 2.0, 4.0]


def test_get_order_401_raises_immediately():
    client = make_client()
    mock_response = MagicMock()
    mock_response.status_code = 401

    with patch.object(client.session, "get", return_value=mock_response):
        with pytest.raises(IFoodAPIError, match="Unauthorized"):
            client.get_order("order-1")
