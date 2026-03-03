import pytest

from crm.models import (
    Campaign,
    CampaignRecipient,
    CampaignStatus,
    CustomerSegment,
    RecipientStatus,
    TenantBillingQuota,
)


@pytest.mark.django_db
class TestCustomerSegment:
    def test_create_segment(self, segment_factory):
        segment = segment_factory(name="VIP", criteria=[{"criteria": "RFV_FREQUENCY_GTE", "value": 5}])
        assert segment.name == "VIP"
        assert len(segment.criteria) == 1

    def test_segment_ordering(self, segment_factory):
        segment_factory(name="Bravo")
        segment_factory(name="Alpha")
        names = list(CustomerSegment.objects.values_list("name", flat=True))
        assert names[0] == "Alpha"

    def test_segment_str(self, segment_factory):
        segment = segment_factory(name="Win-back")
        assert "Win-back" in str(segment)


@pytest.mark.django_db
class TestCampaignTemplate:
    def test_create_template(self, campaign_template_factory):
        tmpl = campaign_template_factory(name="Welcome", channel="EMAIL", body="Oi {{name}}")
        assert tmpl.channel == "EMAIL"
        assert "{{name}}" in tmpl.body

    def test_template_str(self, campaign_template_factory):
        tmpl = campaign_template_factory(name="Promo", channel="WHATSAPP")
        assert "Promo" in str(tmpl)
        assert "WHATSAPP" in str(tmpl)


@pytest.mark.django_db
class TestCampaign:
    def test_create_campaign_default_draft(self, campaign_factory):
        campaign = campaign_factory()
        assert campaign.status == CampaignStatus.DRAFT

    def test_campaign_ordering(self, campaign_factory):
        """Most recent first."""
        c1 = campaign_factory(name="First")
        campaign_factory(name="Second")
        campaigns = list(Campaign.objects.filter(tenant=c1.tenant))
        assert campaigns[0].name == "Second"

    def test_campaign_str(self, campaign_factory):
        campaign = campaign_factory(name="Black Friday")
        assert "Black Friday" in str(campaign)


@pytest.mark.django_db
class TestCampaignRun:
    def test_create_run(self, campaign_run_factory):
        run = campaign_run_factory()
        assert run.status == CampaignStatus.RUNNING
        assert run.total_recipients == 0

    def test_run_counters_default_zero(self, campaign_run_factory):
        run = campaign_run_factory()
        assert run.sent_count == 0
        assert run.delivered_count == 0
        assert run.failed_count == 0
        assert run.opted_out_count == 0


@pytest.mark.django_db
class TestCampaignRecipient:
    def test_create_recipient(self, campaign_recipient_factory):
        recipient = campaign_recipient_factory()
        assert recipient.status == RecipientStatus.PENDING

    def test_unique_run_customer(self, campaign_recipient_factory):
        recipient = campaign_recipient_factory()
        with pytest.raises(Exception):
            CampaignRecipient.objects.create(
                run=recipient.run,
                customer=recipient.customer,
                channel="WHATSAPP",
            )


@pytest.mark.django_db
class TestTenantBillingQuota:
    def test_usage_pct(self, tenant):
        quota = TenantBillingQuota.objects.create(tenant=tenant, max_contacts=100, current_period_contacts=50)
        assert quota.usage_pct == 50.0

    def test_usage_pct_zero_max(self, tenant):
        quota = TenantBillingQuota.objects.create(tenant=tenant, max_contacts=0, current_period_contacts=0)
        assert quota.usage_pct == 100.0

    def test_is_blocked(self, tenant):
        quota = TenantBillingQuota.objects.create(tenant=tenant, max_contacts=10, current_period_contacts=10)
        assert quota.is_blocked is True

    def test_is_not_blocked(self, tenant):
        quota = TenantBillingQuota.objects.create(tenant=tenant, max_contacts=10, current_period_contacts=5)
        assert quota.is_blocked is False

    def test_is_near_limit(self, tenant):
        quota = TenantBillingQuota.objects.create(tenant=tenant, max_contacts=10, current_period_contacts=8)
        assert quota.is_near_limit is True

    def test_not_near_limit(self, tenant):
        quota = TenantBillingQuota.objects.create(tenant=tenant, max_contacts=10, current_period_contacts=5)
        assert quota.is_near_limit is False

    def test_str(self, tenant):
        quota = TenantBillingQuota.objects.create(tenant=tenant, max_contacts=100, current_period_contacts=50)
        assert "50/100" in str(quota)
