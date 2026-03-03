import pytest

from crm.billing import QuotaExceeded, check_and_consume_quota, get_quota_status
from crm.models import TenantBillingQuota


@pytest.mark.django_db
def test_consume_quota_normal(tenant_factory):
    tenant = tenant_factory()
    TenantBillingQuota.objects.create(tenant=tenant, max_contacts=100)
    result = check_and_consume_quota(tenant, quantity=10)
    assert result["current"] == 10
    assert result["usage_pct"] == 10.0


@pytest.mark.django_db
def test_consume_quota_blocks_at_100pct(tenant_factory):
    tenant = tenant_factory()
    TenantBillingQuota.objects.create(tenant=tenant, max_contacts=10, current_period_contacts=10)
    with pytest.raises(QuotaExceeded):
        check_and_consume_quota(tenant, quantity=1)


@pytest.mark.django_db
def test_consume_quota_blocks_when_would_exceed(tenant_factory):
    tenant = tenant_factory()
    TenantBillingQuota.objects.create(tenant=tenant, max_contacts=10, current_period_contacts=9)
    with pytest.raises(QuotaExceeded):
        check_and_consume_quota(tenant, quantity=2)  # 9+2=11 > 10


@pytest.mark.django_db
def test_consume_quota_near_limit_sets_alert(tenant_factory):
    tenant = tenant_factory()
    TenantBillingQuota.objects.create(tenant=tenant, max_contacts=10, current_period_contacts=7)
    result = check_and_consume_quota(tenant, quantity=1)  # 8/10 = 80%
    assert result["near_limit"] is True
    quota = TenantBillingQuota.objects.get(tenant=tenant)
    assert quota.alert_sent_at_80 is not None


@pytest.mark.django_db
def test_quota_never_auto_upgrades(tenant_factory):
    """Garantia: quota nunca altera max_contacts automaticamente."""
    tenant = tenant_factory()
    TenantBillingQuota.objects.create(tenant=tenant, max_contacts=10, current_period_contacts=10)
    try:
        check_and_consume_quota(tenant, quantity=1)
    except QuotaExceeded:
        pass
    quota = TenantBillingQuota.objects.get(tenant=tenant)
    assert quota.max_contacts == 10  # não mudou


@pytest.mark.django_db
def test_get_quota_status(tenant_factory):
    tenant = tenant_factory()
    TenantBillingQuota.objects.create(tenant=tenant, max_contacts=100, current_period_contacts=50)
    result = get_quota_status(tenant)
    assert result["usage_pct"] == 50.0
    assert result["is_blocked"] is False
    assert result["is_near_limit"] is False


@pytest.mark.django_db
def test_get_quota_auto_creates_if_missing(tenant_factory):
    """get_quota_status cria quota com defaults se não existir."""
    tenant = tenant_factory()
    result = get_quota_status(tenant)
    assert result["max_contacts"] == 1000
    assert result["current_period_contacts"] == 0


@pytest.mark.django_db
def test_consume_quota_exact_limit(tenant_factory):
    """Consumir exatamente até o limite é permitido."""
    tenant = tenant_factory()
    TenantBillingQuota.objects.create(tenant=tenant, max_contacts=10, current_period_contacts=0)
    result = check_and_consume_quota(tenant, quantity=10)
    assert result["current"] == 10
    assert result["usage_pct"] == 100.0
