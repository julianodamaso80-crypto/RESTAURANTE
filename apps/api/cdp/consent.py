import structlog

from .models import ConsentRecord, ConsentStatus, Customer, CustomerEvent, CustomerEventType

log = structlog.get_logger()


def get_current_consent(customer: Customer, channel: str) -> str | None:
    """Retorna o status de consentimento mais recente para um canal.

    Retorna None se nunca houve registro.
    """
    record = ConsentRecord.objects.filter(customer=customer, channel=channel).order_by("-created_at").first()
    return record.status if record else None


def has_consent(customer: Customer, channel: str) -> bool:
    """True se o consentimento mais recente para o canal é GRANTED."""
    return get_current_consent(customer, channel) == ConsentStatus.GRANTED


def grant_consent(customer: Customer, channel: str, **kwargs) -> ConsentRecord:
    """Registra consentimento GRANTED. Sempre cria novo registro (append-only)."""
    record = ConsentRecord.objects.create(
        customer=customer,
        channel=channel,
        status=ConsentStatus.GRANTED,
        **kwargs,
    )
    CustomerEvent.objects.create(
        customer=customer,
        event_type=CustomerEventType.CONSENT_GRANTED,
        payload={"channel": channel},
    )
    log.info("consent_granted", customer_id=str(customer.id), channel=channel)
    return record


def revoke_consent(customer: Customer, channel: str, **kwargs) -> ConsentRecord:
    """Registra consentimento REVOKED. Sempre cria novo registro (append-only)."""
    record = ConsentRecord.objects.create(
        customer=customer,
        channel=channel,
        status=ConsentStatus.REVOKED,
        **kwargs,
    )
    CustomerEvent.objects.create(
        customer=customer,
        event_type=CustomerEventType.CONSENT_REVOKED,
        payload={"channel": channel},
    )
    log.info("consent_revoked", customer_id=str(customer.id), channel=channel)
    return record
