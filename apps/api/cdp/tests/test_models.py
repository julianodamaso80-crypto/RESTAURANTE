import pytest
from django.db import IntegrityError

from cdp.models import ConsentStatus, IdentityType


@pytest.mark.django_db
def test_customer_creation(customer_factory):
    c = customer_factory()
    assert c.pk is not None
    assert c.rfv_frequency == 0
    assert c.rfv_monetary_cents == 0


@pytest.mark.django_db
def test_customer_identity_unique(customer_factory, customer_identity_factory):
    customer = customer_factory()
    customer_identity_factory(customer=customer, type=IdentityType.PHONE, value="+5511999999999")
    with pytest.raises(IntegrityError):
        customer_identity_factory(customer=customer, type=IdentityType.PHONE, value="+5511999999999")


@pytest.mark.django_db
def test_consent_record_is_append_only(customer_factory, consent_record_factory):
    """Consent records não podem ser editados — só criados."""
    customer = customer_factory()
    consent_record_factory(customer=customer, status=ConsentStatus.GRANTED)
    consent_record_factory(customer=customer, status=ConsentStatus.REVOKED)
    assert customer.consents.count() == 2


@pytest.mark.django_db
def test_customer_event_append_only(customer_factory, customer_event_factory):
    c = customer_factory()
    customer_event_factory(customer=c)
    customer_event_factory(customer=c)
    assert c.events.count() == 2


@pytest.mark.django_db
def test_customer_str(customer_factory):
    c = customer_factory(phone="+5511999999999")
    assert "+5511999999999" in str(c)


@pytest.mark.django_db
def test_customer_identity_str(customer_identity_factory):
    ci = customer_identity_factory(type=IdentityType.EMAIL, value="test@example.com", is_verified=True)
    s = str(ci)
    assert "EMAIL" in s
    assert "test@example.com" in s
    assert "V" in s


@pytest.mark.django_db
def test_consent_record_str(consent_record_factory):
    cr = consent_record_factory(channel="WHATSAPP", status=ConsentStatus.GRANTED)
    s = str(cr)
    assert "WHATSAPP" in s
    assert "GRANTED" in s


@pytest.mark.django_db
def test_customer_event_str(customer_event_factory):
    ce = customer_event_factory(event_type="ORDER_DELIVERED")
    assert "ORDER_DELIVERED" in str(ce)


@pytest.mark.django_db
def test_customer_identity_different_types_allowed(customer_factory, customer_identity_factory):
    """Same customer can have different identity types with same value."""
    customer = customer_factory()
    customer_identity_factory(customer=customer, type=IdentityType.PHONE, value="123")
    customer_identity_factory(customer=customer, type=IdentityType.EXTERNAL, value="123")
    assert customer.identities.count() == 2
