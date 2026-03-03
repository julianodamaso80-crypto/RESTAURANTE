import structlog
from django.utils import timezone

log = structlog.get_logger()


class QuotaExceeded(Exception):
    """Levantada quando tenant atingiu 100% do teto de contatos."""

    pass


class QuotaNearLimit(Exception):
    """Levantada quando tenant está entre 80-99% (aviso, não bloqueia)."""

    pass


def check_and_consume_quota(tenant, quantity: int = 1) -> dict:
    """Verifica e consome quota de contatos.

    - Se >= 100%: levanta QuotaExceeded (BLOQUEIO — sem upgrade silencioso)
    - Se >= 80%: registra alerta, MAS permite o envio (warning)
    - Caso contrário: consome normalmente

    Retorna dict com status e usage_pct.
    NUNCA faz upgrade automático de plano.
    """
    from .models import TenantBillingQuota

    quota, _ = TenantBillingQuota.objects.get_or_create(
        tenant=tenant,
        defaults={"max_contacts": 1000, "current_period_contacts": 0},
    )

    if quota.current_period_contacts + quantity > quota.max_contacts:
        log.warning(
            "billing_quota_exceeded",
            tenant_id=str(tenant.id),
            current=quota.current_period_contacts,
            max=quota.max_contacts,
            requested=quantity,
        )
        raise QuotaExceeded(
            f"Limite de {quota.max_contacts} contatos atingido. "
            f"Acesse o painel para fazer upgrade do seu plano."
        )

    quota.current_period_contacts += quantity
    quota.save(update_fields=["current_period_contacts", "updated_at"])

    # Alerta em 80%
    if quota.is_near_limit and not quota.alert_sent_at_80:
        quota.alert_sent_at_80 = timezone.now()
        quota.save(update_fields=["alert_sent_at_80", "updated_at"])
        log.warning(
            "billing_quota_80pct_alert",
            tenant_id=str(tenant.id),
            usage_pct=quota.usage_pct,
        )

    return {
        "usage_pct": quota.usage_pct,
        "current": quota.current_period_contacts,
        "max": quota.max_contacts,
        "near_limit": quota.is_near_limit,
    }


def get_quota_status(tenant) -> dict:
    from .models import TenantBillingQuota

    quota, _ = TenantBillingQuota.objects.get_or_create(
        tenant=tenant,
        defaults={"max_contacts": 1000},
    )
    return {
        "max_contacts": quota.max_contacts,
        "current_period_contacts": quota.current_period_contacts,
        "usage_pct": round(quota.usage_pct, 1),
        "is_blocked": quota.is_blocked,
        "is_near_limit": quota.is_near_limit,
    }
