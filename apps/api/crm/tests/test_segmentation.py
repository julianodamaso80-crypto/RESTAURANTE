import pytest

from crm.segmentation import estimate_segment_size, evaluate_segment


@pytest.mark.django_db
def test_segment_all_customers(segment_factory, customer_factory):
    customer_factory()
    customer_factory()
    segment = segment_factory(criteria=[{"criteria": "ALL_CUSTOMERS", "value": None}])
    assert estimate_segment_size(segment) >= 2


@pytest.mark.django_db
def test_segment_rfv_frequency_gte(segment_factory, customer_factory):
    c_low = customer_factory(rfv_frequency=1)
    c_high = customer_factory(rfv_frequency=5)
    segment = segment_factory(criteria=[{"criteria": "RFV_FREQUENCY_GTE", "value": 3}])
    qs = evaluate_segment(segment)
    ids = list(qs.values_list("id", flat=True))
    assert c_high.id in ids
    assert c_low.id not in ids


@pytest.mark.django_db
def test_segment_rfv_recency_lte(segment_factory, customer_factory):
    c_recent = customer_factory(rfv_recency_days=5)
    c_old = customer_factory(rfv_recency_days=60)
    segment = segment_factory(criteria=[{"criteria": "RFV_RECENCY_LTE", "value": 30}])
    qs = evaluate_segment(segment)
    ids = list(qs.values_list("id", flat=True))
    assert c_recent.id in ids
    assert c_old.id not in ids


@pytest.mark.django_db
def test_segment_rfv_monetary_gte(segment_factory, customer_factory):
    c_low = customer_factory(rfv_monetary_cents=500)
    c_high = customer_factory(rfv_monetary_cents=5000)
    segment = segment_factory(criteria=[{"criteria": "RFV_MONETARY_GTE", "value": 1000}])
    qs = evaluate_segment(segment)
    ids = list(qs.values_list("id", flat=True))
    assert c_high.id in ids
    assert c_low.id not in ids


@pytest.mark.django_db
def test_segment_winback(segment_factory, customer_factory):
    """Clientes sem pedido há >= 30 dias."""
    c_inactive = customer_factory(rfv_recency_days=45)
    c_active = customer_factory(rfv_recency_days=5)
    segment = segment_factory(criteria=[{"criteria": "NO_ORDER_SINCE_DAYS", "value": 30}])
    qs = evaluate_segment(segment)
    ids = list(qs.values_list("id", flat=True))
    assert c_inactive.id in ids
    assert c_active.id not in ids


@pytest.mark.django_db
def test_segment_multiple_criteria_and(segment_factory, customer_factory):
    """Múltiplos critérios com AND — só clientes que satisfazem TODOS."""
    c_both = customer_factory(rfv_frequency=5, rfv_monetary_cents=5000)
    c_only_freq = customer_factory(rfv_frequency=5, rfv_monetary_cents=100)
    segment = segment_factory(
        criteria=[
            {"criteria": "RFV_FREQUENCY_GTE", "value": 3},
            {"criteria": "RFV_MONETARY_GTE", "value": 1000},
        ]
    )
    qs = evaluate_segment(segment)
    ids = list(qs.values_list("id", flat=True))
    assert c_both.id in ids
    assert c_only_freq.id not in ids


@pytest.mark.django_db
def test_segment_has_consent(segment_factory, customer_factory, consent_record_factory):
    """HAS_CONSENT filtra por consentimento GRANTED no canal."""
    c_consented = customer_factory()
    c_no_consent = customer_factory()
    consent_record_factory(customer=c_consented, channel="WHATSAPP", status="GRANTED")

    segment = segment_factory(criteria=[{"criteria": "HAS_CONSENT", "value": "WHATSAPP"}])
    qs = evaluate_segment(segment)
    ids = list(qs.values_list("id", flat=True))
    assert c_consented.id in ids
    assert c_no_consent.id not in ids


@pytest.mark.django_db
def test_segment_has_consent_revoked_excluded(segment_factory, customer_factory, consent_record_factory):
    """Consentimento revogado (mais recente) exclui do segmento."""
    from datetime import timedelta

    from django.utils import timezone

    c = customer_factory()
    t1 = timezone.now()
    t2 = t1 + timedelta(seconds=1)
    consent_record_factory(customer=c, channel="WHATSAPP", status="GRANTED", created_at=t1)
    consent_record_factory(customer=c, channel="WHATSAPP", status="REVOKED", created_at=t2)

    segment = segment_factory(criteria=[{"criteria": "HAS_CONSENT", "value": "WHATSAPP"}])
    qs = evaluate_segment(segment)
    ids = list(qs.values_list("id", flat=True))
    assert c.id not in ids


@pytest.mark.django_db
def test_segment_only_active_customers(segment_factory, customer_factory):
    """Apenas clientes is_active=True são incluídos."""
    c_active = customer_factory(is_active=True)
    c_inactive = customer_factory(is_active=False)
    segment = segment_factory(criteria=[{"criteria": "ALL_CUSTOMERS", "value": None}])
    qs = evaluate_segment(segment)
    ids = list(qs.values_list("id", flat=True))
    assert c_active.id in ids
    assert c_inactive.id not in ids


@pytest.mark.django_db
def test_estimate_segment_size(segment_factory, customer_factory):
    customer_factory()
    customer_factory()
    customer_factory()
    segment = segment_factory(criteria=[{"criteria": "ALL_CUSTOMERS", "value": None}])
    assert estimate_segment_size(segment) == 3
