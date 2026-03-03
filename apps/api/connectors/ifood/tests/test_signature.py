import hashlib
import hmac
import inspect

from connectors.ifood import signature
from connectors.ifood.signature import verify_signature

SECRET = "test-secret-key"


def make_signature(payload: bytes, secret: str) -> str:
    return hmac.new(
        key=secret.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()


def test_valid_signature():
    payload = b'{"id": "event-1"}'
    sig = make_signature(payload, SECRET)
    assert verify_signature(payload, sig, SECRET) is True


def test_invalid_signature():
    payload = b'{"id": "event-1"}'
    assert verify_signature(payload, "invalida", SECRET) is False


def test_tampered_payload():
    original = b'{"id": "event-1"}'
    sig = make_signature(original, SECRET)
    tampered = b'{"id": "event-HACKED"}'
    assert verify_signature(tampered, sig, SECRET) is False


def test_empty_signature():
    assert verify_signature(b"payload", "", SECRET) is False


def test_empty_secret():
    assert verify_signature(b"payload", "any-sig", "") is False


def test_both_empty():
    assert verify_signature(b"", "", "") is False


def test_compare_digest_timing_safe():
    """Ensures compare_digest (timing-safe) is used, not == directly."""
    source = inspect.getsource(signature)
    assert "compare_digest" in source
