import os
import time

import requests
import structlog

log = structlog.get_logger()

RAPPI_STUB_MODE = os.environ.get("RAPPI_STUB_MODE", "false").lower() in ("true", "1", "yes")

RAPPI_BASE_URL_PROD = "https://microservices.rappi.com.br/api/v2/restaurants-integrations-public-api"


class RappiAPIError(Exception):
    pass


class RappiOrderNotFoundError(RappiAPIError):
    """404 transient — should be retried with backoff."""


class RappiAPIClient:
    """HTTP client for Rappi API.

    Auth: x-authorization: Bearer <TOKEN> (static token, no OAuth).
    Stub mode: if RAPPI_STUB_MODE=true, returns fake data.
    """

    def __init__(self, rappi_token: str, base_url: str = RAPPI_BASE_URL_PROD):
        self.rappi_token = rappi_token
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "x-authorization": f"Bearer {rappi_token}",
            "Content-Type": "application/json",
        })

    def get_orders(self) -> list[dict]:
        """Fetch pending orders from Rappi."""
        if RAPPI_STUB_MODE:
            return _stub_orders()

        url = f"{self.base_url}/orders"
        response = self.session.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        response.raise_for_status()
        return []

    def get_order(self, order_id: str, max_retries: int = 3, base_delay: float = 1.0) -> dict:
        """Fetch order details with retry for transient 404."""
        if RAPPI_STUB_MODE:
            return _stub_order_detail(order_id)

        url = f"{self.base_url}/orders/{order_id}"

        for attempt in range(max_retries + 1):
            try:
                response = self.session.get(url, timeout=10)

                if response.status_code == 200:
                    log.info("rappi_order_fetched", order_id=order_id, attempt=attempt)
                    return response.json()

                if response.status_code == 404:
                    if attempt < max_retries:
                        delay = base_delay * (2**attempt)
                        log.warning("rappi_order_not_found_retry", order_id=order_id, attempt=attempt, retry_in=delay)
                        time.sleep(delay)
                        continue
                    else:
                        raise RappiOrderNotFoundError(f"Order {order_id} not found after {max_retries} retries")

                if response.status_code == 401:
                    raise RappiAPIError(f"Unauthorized — invalid token for order {order_id}")

                response.raise_for_status()

            except (requests.Timeout, requests.ConnectionError) as exc:
                if attempt < max_retries:
                    delay = base_delay * (2**attempt)
                    log.warning("rappi_order_fetch_network_error", order_id=order_id, attempt=attempt, error=str(exc))
                    time.sleep(delay)
                    continue
                raise RappiAPIError(f"Network error fetching order {order_id}: {exc}")

        raise RappiAPIError(f"Unexpected exit from retry loop for order {order_id}")

    def accept_order(self, order_id: str, cooking_time: int = 20) -> bool:
        """Accept an order with cooking time in minutes."""
        if RAPPI_STUB_MODE:
            log.info("rappi_stub_accept_order", order_id=order_id, cooking_time=cooking_time)
            return True

        url = f"{self.base_url}/orders/{order_id}/take/{cooking_time}"
        response = self.session.put(url, timeout=10)
        return 200 <= response.status_code < 300

    def reject_order(self, order_id: str) -> bool:
        """Reject an order."""
        if RAPPI_STUB_MODE:
            log.info("rappi_stub_reject_order", order_id=order_id)
            return True

        url = f"{self.base_url}/orders/{order_id}/reject"
        response = self.session.put(url, timeout=10)
        return 200 <= response.status_code < 300

    def get_stores(self) -> list[dict]:
        """List partner stores."""
        if RAPPI_STUB_MODE:
            return [{"storeId": "STUB-001", "name": "Stub Store", "integrated": True}]

        url = f"{self.base_url}/stores-pa"
        response = self.session.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        response.raise_for_status()
        return []

    def register_webhook(self, webhook_url: str, store_ids: list[str]) -> bool:
        """Register webhook URL for NEW_ORDER events."""
        if RAPPI_STUB_MODE:
            log.info("rappi_stub_register_webhook", url=webhook_url, stores=store_ids)
            return True

        url = f"{self.base_url}/webhook/NEW_ORDER/change-url"
        payload = {"url": webhook_url, "stores": store_ids}
        response = self.session.put(url, json=payload, timeout=10)
        return 200 <= response.status_code < 300

    def check_connection(self) -> bool:
        """Verify that the token is valid by listing stores."""
        try:
            if RAPPI_STUB_MODE:
                return True
            stores = self.get_stores()
            return isinstance(stores, list)
        except Exception:
            return False


def _stub_orders() -> list[dict]:
    return [
        {
            "id": "rappi-stub-order-001",
            "store_id": "STUB-001",
            "total_value": 45.90,
            "items": [{"name": "X-Burger Rappi", "quantity": 1, "unit_price": 45.90, "total_price": 45.90}],
        }
    ]


def _stub_order_detail(order_id: str) -> dict:
    return {
        "id": order_id,
        "store_id": "STUB-001",
        "displayId": f"#R{order_id[-4:]}",
        "delivery": {"mode": "DELIVERY", "deliveryFee": 5.00},
        "subTotal": 45.90,
        "totalPrice": 50.90,
        "totalDiscount": 0.0,
        "items": [
            {
                "id": "item-rappi-001",
                "externalCode": "SKU-R1",
                "name": "X-Burger Rappi",
                "quantity": 1,
                "unitPrice": 45.90,
                "totalPrice": 45.90,
                "observations": "",
            }
        ],
    }
