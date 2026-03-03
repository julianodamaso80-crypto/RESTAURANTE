import structlog
import structlog.contextvars
from celery import shared_task
from django.db.models import F, OuterRef, Subquery
from django.utils import timezone

log = structlog.get_logger()


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def execute_campaign_run(self, campaign_run_id: str):
    """Executa uma CampaignRun:

    1. Avalia segmento → lista de customers
    2. Filtra só customers com consentimento no canal
    3. Checa billing quota (bloqueia se 100%)
    4. Cria CampaignRecipient para cada um
    5. Dispara send_campaign_message para cada recipient
    """
    from cdp.models import ConsentRecord, ConsentStatus

    from .billing import QuotaExceeded, check_and_consume_quota
    from .models import CampaignRecipient, CampaignRun, CampaignStatus, RecipientStatus
    from .segmentation import evaluate_segment

    structlog.contextvars.bind_contextvars(campaign_run_id=campaign_run_id)

    try:
        run = CampaignRun.objects.select_related(
            "campaign__segment", "campaign__template", "campaign__tenant"
        ).get(id=campaign_run_id)
    except CampaignRun.DoesNotExist:
        log.error("campaign_run_not_found")
        return

    campaign = run.campaign
    tenant = campaign.tenant
    channel = campaign.template.channel

    log.info("campaign_run_started", campaign_id=str(campaign.id))

    # 1. Avaliar segmento
    customers_qs = evaluate_segment(campaign.segment)

    # 2. Filtrar por consentimento no canal (Subquery compatível com SQLite)
    latest_consent_status = (
        ConsentRecord.objects.filter(
            customer_id=OuterRef("pk"),
            channel=channel,
        )
        .order_by("-created_at")
        .values("status")[:1]
    )
    eligible_qs = customers_qs.annotate(_campaign_consent=Subquery(latest_consent_status)).filter(
        _campaign_consent=ConsentStatus.GRANTED,
    )

    eligible = list(eligible_qs)
    run.total_recipients = len(eligible)
    run.save(update_fields=["total_recipients"])

    if not eligible:
        run.status = CampaignStatus.COMPLETED
        run.completed_at = timezone.now()
        run.save(update_fields=["status", "completed_at"])
        log.info("campaign_run_no_eligible_recipients")
        return

    # 3. Checar billing quota
    try:
        check_and_consume_quota(tenant, quantity=len(eligible))
    except QuotaExceeded as e:
        run.status = CampaignStatus.CANCELLED
        run.error_detail = str(e)
        run.completed_at = timezone.now()
        run.save(update_fields=["status", "error_detail", "completed_at"])
        log.warning("campaign_run_blocked_by_quota", error=str(e))
        return

    # 4. Criar recipients e disparar tasks individuais
    for customer in eligible:
        destination = _get_destination(customer, channel)

        recipient, created = CampaignRecipient.objects.get_or_create(
            run=run,
            customer=customer,
            defaults={
                "status": RecipientStatus.PENDING,
                "channel": channel,
                "destination": destination,
            },
        )

        if created:
            send_campaign_message.delay(str(recipient.id))

    log.info(
        "campaign_run_recipients_enqueued",
        total=len(eligible),
        run_id=campaign_run_id,
    )


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_campaign_message(self, recipient_id: str):
    """Envia mensagem para um CampaignRecipient individual.

    Usa adapter de canal (stub em dev, real em prod).
    """
    from .adapters.stub import get_adapter
    from .models import CampaignRecipient, RecipientStatus

    structlog.contextvars.bind_contextvars(recipient_id=recipient_id)

    try:
        recipient = CampaignRecipient.objects.select_related(
            "run__campaign__template", "customer"
        ).get(id=recipient_id)
    except CampaignRecipient.DoesNotExist:
        log.error("recipient_not_found")
        return

    if recipient.status != RecipientStatus.PENDING:
        log.info("recipient_already_processed", status=recipient.status)
        return

    template = recipient.run.campaign.template
    customer = recipient.customer

    # Renderizar mensagem com variáveis
    message = _render_template(template.body, customer, recipient.run.campaign)
    subject = template.subject

    # Enviar via adapter
    adapter = get_adapter(recipient.channel)
    result = adapter.send(
        destination=recipient.destination,
        message=message,
        subject=subject,
    )

    if result["success"]:
        recipient.status = RecipientStatus.SENT
        recipient.sent_at = timezone.now()
        recipient.run.__class__.objects.filter(id=recipient.run_id).update(sent_count=F("sent_count") + 1)
    else:
        recipient.status = RecipientStatus.FAILED
        recipient.error_detail = result.get("error", "")
        recipient.run.__class__.objects.filter(id=recipient.run_id).update(failed_count=F("failed_count") + 1)

    recipient.save(update_fields=["status", "sent_at", "error_detail"])
    log.info(
        "campaign_message_sent",
        recipient_id=recipient_id,
        success=result["success"],
    )


def _render_template(body: str, customer, campaign) -> str:
    """Substitui variáveis no template."""
    replacements = {
        "{{name}}": customer.name or "cliente",
        "{{store_name}}": campaign.store.name if campaign.store else "",
        "{{phone}}": customer.phone or "",
    }
    for var, val in replacements.items():
        body = body.replace(var, val)
    return body


def _get_destination(customer, channel: str) -> str:
    from cdp.models import IdentityType

    if channel in ("WHATSAPP", "SMS"):
        identity = customer.identities.filter(type=IdentityType.PHONE, is_verified=True).first()
        return identity.value if identity else customer.phone
    if channel == "EMAIL":
        identity = customer.identities.filter(type=IdentityType.EMAIL, is_verified=True).first()
        return identity.value if identity else customer.email
    return ""
