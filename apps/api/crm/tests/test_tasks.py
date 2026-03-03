from unittest.mock import MagicMock, patch

import pytest

from crm.models import CampaignStatus, RecipientStatus


@pytest.mark.django_db
def test_execute_campaign_run_nonexistent_does_not_crash():
    from crm.tasks import execute_campaign_run

    execute_campaign_run("00000000-0000-0000-0000-000000000000")


@pytest.mark.django_db
def test_execute_campaign_run_blocked_by_quota(campaign_run_factory):
    from crm.billing import QuotaExceeded
    from crm.tasks import execute_campaign_run

    run = campaign_run_factory()

    with patch("crm.billing.check_and_consume_quota", side_effect=QuotaExceeded("Limite atingido")):
        with patch("crm.segmentation.evaluate_segment") as mock_seg:
            # Return a queryset-like list with at least one customer
            mock_customer = MagicMock()
            mock_customer.id = "fake-id"
            mock_customer.pk = "fake-id"
            mock_qs = MagicMock()
            mock_qs.annotate.return_value = mock_qs
            mock_qs.filter.return_value = mock_qs
            mock_qs.__iter__ = MagicMock(return_value=iter([mock_customer]))
            mock_qs.__len__ = MagicMock(return_value=1)
            mock_seg.return_value = mock_qs
            execute_campaign_run(str(run.id))

    run.refresh_from_db()
    assert run.status == CampaignStatus.CANCELLED
    assert "Limite" in run.error_detail


@pytest.mark.django_db
def test_send_campaign_message_stub(campaign_recipient_factory):
    from crm.tasks import send_campaign_message

    recipient = campaign_recipient_factory(status=RecipientStatus.PENDING)
    send_campaign_message(str(recipient.id))
    recipient.refresh_from_db()
    assert recipient.status == RecipientStatus.SENT
    assert recipient.sent_at is not None


@pytest.mark.django_db
def test_send_campaign_message_idempotent(campaign_recipient_factory):
    """Recipient já enviado não é processado novamente."""
    from django.utils import timezone

    from crm.tasks import send_campaign_message

    recipient = campaign_recipient_factory(status=RecipientStatus.SENT)
    recipient.sent_at = timezone.now()
    recipient.save()
    original_sent_at = recipient.sent_at
    send_campaign_message(str(recipient.id))
    recipient.refresh_from_db()
    assert recipient.sent_at == original_sent_at


@pytest.mark.django_db
def test_send_campaign_message_nonexistent_does_not_crash():
    from crm.tasks import send_campaign_message

    send_campaign_message("00000000-0000-0000-0000-000000000000")


@pytest.mark.django_db
def test_tasks_registered_in_celery():
    from config.celery import app

    assert "crm.tasks.execute_campaign_run" in app.tasks
    assert "crm.tasks.send_campaign_message" in app.tasks


@pytest.mark.django_db
def test_send_campaign_message_renders_template(campaign_recipient_factory, customer_factory):
    """Template variables are replaced in message."""
    from crm.tasks import _render_template

    customer = customer_factory(name="João")
    campaign = MagicMock()
    campaign.store = MagicMock()
    campaign.store.name = "Pizzaria Boa"

    result = _render_template("Oi {{name}}, visite {{store_name}}!", customer, campaign)
    assert "João" in result
    assert "Pizzaria Boa" in result
