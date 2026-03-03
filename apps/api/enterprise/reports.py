import structlog
from django.db.models import Count, Sum

log = structlog.get_logger()


def generate_network_report(company_id: str, period: str, date_from, date_to) -> dict:
    """
    Gera relatório consolidado da rede para o período.
    Retorna dict com métricas por store.
    """
    from cdp.models import Customer
    from orders.enums import OrderStatus
    from orders.models import Order
    from stock.models import StockAlert
    from tenants.models import Company, Store

    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return {}

    stores = Store.objects.filter(company=company)
    report_data = {
        "company": company.name,
        "period": period,
        "date_from": str(date_from),
        "date_to": str(date_to),
        "stores": {},
        "network_totals": {},
    }

    total_orders = 0
    total_revenue = 0

    for store in stores:
        orders_qs = Order.objects.filter(
            store=store,
            status=OrderStatus.DELIVERED,
            delivered_at__date__gte=date_from,
            delivered_at__date__lte=date_to,
        )
        orders_stats = orders_qs.aggregate(
            count=Count("id"),
            revenue=Sum("total_cents"),
        )

        orders_count = orders_stats["count"] or 0
        revenue_cents = orders_stats["revenue"] or 0

        stock_alerts = StockAlert.objects.filter(store=store, is_resolved=False).count()

        active_customers = Customer.objects.filter(
            tenant=company.tenant,
            rfv_recency_days__lte=30,
        ).count()

        report_data["stores"][str(store.id)] = {
            "store_name": store.name,
            "orders_count": orders_count,
            "revenue_cents": revenue_cents,
            "revenue_brl": round(revenue_cents / 100, 2),
            "stock_alerts_open": stock_alerts,
            "active_customers": active_customers,
        }

        total_orders += orders_count
        total_revenue += revenue_cents

    report_data["network_totals"] = {
        "total_orders": total_orders,
        "total_revenue_cents": total_revenue,
        "total_revenue_brl": round(total_revenue / 100, 2),
        "stores_count": stores.count(),
    }

    return report_data


def check_network_alerts(company_id: str):
    """
    Verifica alertas da rede e cria NetworkAlert para situações críticas.
    Chamado periodicamente (ou via endpoint manual).
    """
    from kds.models import KDSTicket, KDSTicketStatus
    from stock.models import StockAlert
    from tenants.models import Company, Store

    from .models import NetworkAlert, NetworkAlertType

    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return 0

    stores = Store.objects.filter(company=company)
    alerts_created = 0

    for store in stores:
        critical_stock = StockAlert.objects.filter(store=store, is_resolved=False).count()

        if critical_stock >= 3:
            _, created = NetworkAlert.objects.get_or_create(
                company=company,
                store=store,
                alert_type=NetworkAlertType.STOCK_CRITICAL,
                is_resolved=False,
                defaults={"payload": {"items_below_minimum": critical_stock}},
            )
            if created:
                alerts_created += 1

        kds_backlog = KDSTicket.objects.filter(
            station__store=store,
            status=KDSTicketStatus.WAITING,
        ).count()

        if kds_backlog >= 10:
            _, created = NetworkAlert.objects.get_or_create(
                company=company,
                store=store,
                alert_type=NetworkAlertType.KDS_BACKLOG,
                is_resolved=False,
                defaults={"payload": {"waiting_tickets": kds_backlog}},
            )
            if created:
                alerts_created += 1

    log.info(
        "network_alerts_checked",
        company=company.name,
        stores=stores.count(),
        alerts_created=alerts_created,
    )
    return alerts_created
