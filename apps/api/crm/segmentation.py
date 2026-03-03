import structlog
from django.db.models import OuterRef, Subquery

from cdp.models import ConsentRecord, ConsentStatus, Customer

log = structlog.get_logger()


def evaluate_segment(segment):
    """Avalia os critérios do segmento e retorna queryset de Customers elegíveis.

    Critérios são avaliados com AND (todos devem ser satisfeitos).
    """
    qs = Customer.objects.filter(tenant=segment.tenant, is_active=True)

    for criterion in segment.criteria:
        criteria_type = criterion.get("criteria")
        value = criterion.get("value")

        if criteria_type == "ALL_CUSTOMERS":
            pass  # sem filtro adicional

        elif criteria_type == "RFV_RECENCY_LTE":
            qs = qs.filter(rfv_recency_days__lte=int(value))

        elif criteria_type == "RFV_FREQUENCY_GTE":
            qs = qs.filter(rfv_frequency__gte=int(value))

        elif criteria_type == "RFV_MONETARY_GTE":
            qs = qs.filter(rfv_monetary_cents__gte=int(value))

        elif criteria_type == "NO_ORDER_SINCE_DAYS":
            qs = qs.filter(rfv_recency_days__gte=int(value))

        elif criteria_type == "HAS_CONSENT":
            # Subquery: status do consentimento mais recente por cliente no canal.
            # Compatível com SQLite (sem DISTINCT ON).
            latest_consent_status = (
                ConsentRecord.objects.filter(
                    customer_id=OuterRef("pk"),
                    channel=value,
                )
                .order_by("-created_at")
                .values("status")[:1]
            )
            qs = qs.annotate(_latest_consent=Subquery(latest_consent_status)).filter(
                _latest_consent=ConsentStatus.GRANTED,
            )

    log.info(
        "segment_evaluated",
        segment_id=str(segment.id),
        criteria_count=len(segment.criteria),
        result_count=qs.count(),
    )

    return qs


def estimate_segment_size(segment) -> int:
    """Conta quantos clientes estão no segmento agora."""
    return evaluate_segment(segment).count()
