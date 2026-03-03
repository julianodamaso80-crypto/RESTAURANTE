import time

import requests
import structlog

log = structlog.get_logger()

IFOOD_API_BASE = "https://merchant-api.ifood.com.br"


class IFoodAPIError(Exception):
    pass


class IFoodOrderNotFoundError(IFoodAPIError):
    """404 transient — should be retried with backoff."""


class IFoodAPIClient:
    """HTTP client for the iFood API.

    Implements retry with exponential backoff for transient 404s.
    """

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
        )

    def get_order(self, order_id: str, max_retries: int = 3, base_delay: float = 1.0) -> dict:
        """Fetch order details from iFood.

        Controlled retry for transient 404:
        - iFood may return 404 for a brief window after order creation
        - Exponential backoff: 1s, 2s, 4s
        - After max_retries, raises IFoodOrderNotFoundError
        """
        url = f"{IFOOD_API_BASE}/order/v1.0/orders/{order_id}"

        for attempt in range(max_retries + 1):
            try:
                response = self.session.get(url, timeout=10)

                if response.status_code == 200:
                    log.info("ifood_order_fetched", order_id=order_id, attempt=attempt)
                    return response.json()

                if response.status_code == 404:
                    if attempt < max_retries:
                        delay = base_delay * (2**attempt)
                        log.warning(
                            "ifood_order_not_found_retry",
                            order_id=order_id,
                            attempt=attempt,
                            retry_in=delay,
                        )
                        time.sleep(delay)
                        continue
                    else:
                        raise IFoodOrderNotFoundError(f"Order {order_id} not found after {max_retries} retries")

                if response.status_code == 401:
                    raise IFoodAPIError(f"Unauthorized — expired token for order {order_id}")

                response.raise_for_status()

            except (requests.Timeout, requests.ConnectionError) as exc:
                if attempt < max_retries:
                    delay = base_delay * (2**attempt)
                    log.warning(
                        "ifood_order_fetch_network_error",
                        order_id=order_id,
                        attempt=attempt,
                        error=str(exc),
                        retry_in=delay,
                    )
                    time.sleep(delay)
                    continue
                raise IFoodAPIError(f"Network error fetching order {order_id}: {exc}")

        raise IFoodAPIError(f"Unexpected exit from retry loop for order {order_id}")
