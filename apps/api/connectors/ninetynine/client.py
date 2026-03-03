import time

import requests
import structlog

log = structlog.get_logger()

NINETYNINE_API_BASE = "https://api.99app.com/v1"


class NinetyNineAPIError(Exception):
    pass


class NinetyNineOrderNotFoundError(NinetyNineAPIError):
    """404 transient — should be retried with backoff."""


class NinetyNineAPIClient:
    """HTTP client for 99Food API.

    Retry with exponential backoff for transient 404.
    Same interface as IFoodAPIClient — Open Delivery standardized this.
    """

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        })

    def get_order(self, order_id: str, max_retries: int = 3, base_delay: float = 1.0) -> dict:
        """Fetch order details from 99Food API.

        Controlled retry for transient 404: 1s -> 2s -> 4s.
        """
        url = f"{NINETYNINE_API_BASE}/orders/{order_id}"

        for attempt in range(max_retries + 1):
            try:
                response = self.session.get(url, timeout=10)

                if response.status_code == 200:
                    log.info("99food_order_fetched", order_id=order_id, attempt=attempt)
                    return response.json()

                if response.status_code == 404:
                    if attempt < max_retries:
                        delay = base_delay * (2**attempt)
                        log.warning(
                            "99food_order_not_found_retry",
                            order_id=order_id,
                            attempt=attempt,
                            retry_in=delay,
                        )
                        time.sleep(delay)
                        continue
                    else:
                        raise NinetyNineOrderNotFoundError(
                            f"Order {order_id} not found after {max_retries} retries"
                        )

                if response.status_code == 401:
                    raise NinetyNineAPIError(f"Unauthorized — expired token for order {order_id}")

                response.raise_for_status()

            except (requests.Timeout, requests.ConnectionError) as exc:
                if attempt < max_retries:
                    delay = base_delay * (2**attempt)
                    log.warning(
                        "99food_order_fetch_network_error",
                        order_id=order_id,
                        attempt=attempt,
                        error=str(exc),
                        retry_in=delay,
                    )
                    time.sleep(delay)
                    continue
                raise NinetyNineAPIError(f"Network error fetching order {order_id}: {exc}")

        raise NinetyNineAPIError(f"Unexpected exit from retry loop for order {order_id}")
