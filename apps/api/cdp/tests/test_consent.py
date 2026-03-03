import pytest

from cdp.consent import get_current_consent, grant_consent, has_consent, revoke_consent
from cdp.models import ConsentChannel, ConsentStatus, CustomerEventType


@pytest.mark.django_db
def test_grant_consent(customer_factory):
    c = customer_factory()
    record = grant_consent(c, ConsentChannel.WHATSAPP, source="test")
    assert record.status == ConsentStatus.GRANTED
    assert has_consent(c, ConsentChannel.WHATSAPP) is True


@pytest.mark.django_db
def test_revoke_consent(customer_factory):
    from datetime import timedelta

    from django.utils import timezone

    from cdp.models import ConsentRecord

    c = customer_factory()
    r1 = grant_consent(c, ConsentChannel.WHATSAPP, source="test")
    r2 = revoke_consent(c, ConsentChannel.WHATSAPP, source="test")
    # Ensure deterministic ordering (SQLite same-millisecond issue)
    base = timezone.now()
    ConsentRecord.objects.filter(pk=r1.pk).update(created_at=base - timedelta(seconds=1))
    ConsentRecord.objects.filter(pk=r2.pk).update(created_at=base)
    assert has_consent(c, ConsentChannel.WHATSAPP) is False


@pytest.mark.django_db
def test_no_consent_returns_false(customer_factory):
    c = customer_factory()
    assert has_consent(c, ConsentChannel.EMAIL) is False


@pytest.mark.django_db
def test_consent_history_preserved(customer_factory):
    """Revogar não apaga o grant anterior — ambos ficam no histórico."""
    c = customer_factory()
    grant_consent(c, ConsentChannel.SMS, source="test")
    revoke_consent(c, ConsentChannel.SMS, source="test")
    assert c.consents.filter(channel=ConsentChannel.SMS).count() == 2


@pytest.mark.django_db
def test_current_consent_is_most_recent(customer_factory):
    from datetime import timedelta

    from django.utils import timezone as tz

    from cdp.models import ConsentRecord

    c = customer_factory()
    r1 = grant_consent(c, ConsentChannel.PUSH, source="test")
    r2 = revoke_consent(c, ConsentChannel.PUSH, source="test")
    r3 = grant_consent(c, ConsentChannel.PUSH, source="test")

    # Ensure deterministic ordering with explicit timestamps
    base = tz.now()
    ConsentRecord.objects.filter(pk=r1.pk).update(created_at=base - timedelta(seconds=2))
    ConsentRecord.objects.filter(pk=r2.pk).update(created_at=base - timedelta(seconds=1))
    ConsentRecord.objects.filter(pk=r3.pk).update(created_at=base)

    assert get_current_consent(c, ConsentChannel.PUSH) == ConsentStatus.GRANTED


@pytest.mark.django_db
def test_consent_creates_customer_event(customer_factory):
    c = customer_factory()
    grant_consent(c, ConsentChannel.WHATSAPP, source="test")
    assert c.events.filter(event_type=CustomerEventType.CONSENT_GRANTED).exists()


@pytest.mark.django_db
def test_revoke_creates_customer_event(customer_factory):
    c = customer_factory()
    revoke_consent(c, ConsentChannel.EMAIL, source="test")
    assert c.events.filter(event_type=CustomerEventType.CONSENT_REVOKED).exists()


@pytest.mark.django_db
def test_get_current_consent_returns_none_if_no_records(customer_factory):
    c = customer_factory()
    assert get_current_consent(c, ConsentChannel.PUSH) is None


@pytest.mark.django_db
def test_consent_per_channel_independent(customer_factory):
    """Consentimento em um canal não afeta outro."""
    c = customer_factory()
    grant_consent(c, ConsentChannel.WHATSAPP, source="test")
    assert has_consent(c, ConsentChannel.WHATSAPP) is True
    assert has_consent(c, ConsentChannel.EMAIL) is False
