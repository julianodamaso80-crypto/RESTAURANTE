import structlog
from celery import shared_task

log = structlog.get_logger()


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def run_franchisee_onboarding(self, onboarding_id: str):
    """Executa onboarding de nova store assincronamente."""
    from .onboarding import run_onboarding

    structlog.contextvars.bind_contextvars(onboarding_id=onboarding_id)
    run_onboarding(onboarding_id)


@shared_task(bind=True, max_retries=2)
def generate_network_report_task(self, company_id: str, period: str, date_from_str: str, date_to_str: str):
    """Gera relatório da rede assincronamente."""
    from datetime import date

    from django.utils import timezone

    from .models import NetworkReport
    from .reports import generate_network_report

    date_from = date.fromisoformat(date_from_str)
    date_to = date.fromisoformat(date_to_str)

    data = generate_network_report(company_id, period, date_from, date_to)

    NetworkReport.objects.update_or_create(
        company_id=company_id,
        period=period,
        date_from=date_from,
        defaults={
            "date_to": date_to,
            "data": data,
            "generated_at": timezone.now(),
        },
    )
    log.info("network_report_generated", company_id=company_id, period=period)


@shared_task(bind=True)
def check_network_alerts_task(self, company_id: str):
    """Verifica e cria alertas da rede."""
    from .reports import check_network_alerts

    count = check_network_alerts(company_id)
    log.info("network_alerts_task_done", company_id=company_id, alerts=count)
