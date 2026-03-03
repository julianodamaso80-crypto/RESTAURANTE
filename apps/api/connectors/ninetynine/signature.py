import hashlib
import hmac

import structlog

log = structlog.get_logger()


def verify_signature(payload_bytes: bytes, signature_header: str, secret: str) -> bool:
    """Validate X-Ninetynine-Signature (HMAC SHA256).

    Same algorithm as iFood — Open Delivery Protocol standardized this.

    Returns True if valid, False otherwise.
    NEVER raises — returns False on any error.
    """
    if not signature_header or not secret:
        log.warning("99food_signature_missing", has_header=bool(signature_header), has_secret=bool(secret))
        return False

    try:
        expected = hmac.new(
            key=secret.encode("utf-8"),
            msg=payload_bytes,
            digestmod=hashlib.sha256,
        ).hexdigest()

        valid = hmac.compare_digest(expected, signature_header.strip())

        if not valid:
            log.warning("99food_signature_invalid")

        return valid
    except Exception as exc:
        log.error("99food_signature_error", error=str(exc))
        return False
