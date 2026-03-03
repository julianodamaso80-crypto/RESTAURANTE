import hashlib
import hmac

from connectors.ninetynine.signature import verify_signature

SECRET = "test-secret-99food"


def make_sig(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def test_valid_signature():
    payload = b'{"id": "evt-99-1"}'
    assert verify_signature(payload, make_sig(payload, SECRET), SECRET) is True


def test_invalid_signature():
    payload = b'{"id": "evt-99-1"}'
    assert verify_signature(payload, "invalida", SECRET) is False


def test_tampered_payload():
    original = b'{"id": "evt-99-1"}'
    sig = make_sig(original, SECRET)
    assert verify_signature(b'{"id": "HACKED"}', sig, SECRET) is False


def test_empty_signature():
    assert verify_signature(b"payload", "", SECRET) is False


def test_empty_secret():
    assert verify_signature(b"payload", "sig", "") is False


def test_uses_compare_digest():
    import inspect

    from connectors.ninetynine import signature

    assert "compare_digest" in inspect.getsource(signature)
