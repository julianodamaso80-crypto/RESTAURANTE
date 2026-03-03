import structlog
from django.db.models.signals import post_save
from django.dispatch import receiver

log = structlog.get_logger()


@receiver(post_save, sender="orders.Order")
def create_kds_tickets_on_confirm(sender, instance, **kwargs):
    """Create KDSTickets when an Order moves to CONFIRMED or IN_PREPARATION.

    Idempotent: uses get_or_create.
    """
    from orders.enums import OrderStatus

    from .models import KDSStation, KDSTicket, KDSTicketStatus

    if instance.status not in (OrderStatus.CONFIRMED, OrderStatus.IN_PREPARATION):
        return

    stations = KDSStation.objects.filter(store=instance.store, is_active=True)

    for station in stations:
        if station.filter_order_types and instance.order_type not in station.filter_order_types:
            continue

        ticket, created = KDSTicket.objects.get_or_create(
            station=station,
            order=instance,
            defaults={"status": KDSTicketStatus.WAITING},
        )

        if created:
            log.info(
                "kds_ticket_created",
                ticket_id=str(ticket.id),
                order_id=str(instance.id),
                station=station.name,
            )
