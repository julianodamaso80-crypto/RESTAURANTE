import uuid

from django.db import models
from django.utils import timezone


class KDSStationCategory(models.TextChoices):
    GRILL = "GRILL", "Chapa/Grill"
    COLD = "COLD", "Frio/Saladas"
    DRINKS = "DRINKS", "Bebidas"
    DESSERTS = "DESSERTS", "Sobremesas"
    GENERAL = "GENERAL", "Geral"
    PACKING = "PACKING", "Embalagem/Expedição"


class KDSTicketStatus(models.TextChoices):
    WAITING = "WAITING", "Aguardando"
    IN_PROGRESS = "IN_PROGRESS", "Em preparo"
    DONE = "DONE", "Concluído"


class KDSStation(models.Model):
    """Kitchen workstation (e.g. grill, cold, drinks).

    A store can have multiple stations.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store = models.ForeignKey("tenants.Store", on_delete=models.CASCADE, related_name="kds_stations")
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=KDSStationCategory.choices, default=KDSStationCategory.GENERAL)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0, help_text="Display order in the panel")
    filter_order_types = models.JSONField(
        default=list,
        blank=True,
        help_text="List of order_type this station displays. Empty = all.",
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]
        unique_together = [("store", "name")]

    def __str__(self):
        return f"{self.name} ({self.category}) — Store {self.store_id}"


class KDSTicket(models.Model):
    """An Order displayed on a KDS station.

    The same Order can generate tickets on multiple stations.
    Records timestamps for prep time calculation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    station = models.ForeignKey(KDSStation, on_delete=models.CASCADE, related_name="tickets")
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="kds_tickets")

    status = models.CharField(max_length=20, choices=KDSTicketStatus.choices, default=KDSTicketStatus.WAITING)

    enqueued_at = models.DateTimeField(default=timezone.now, help_text="When it entered the station queue")
    started_at = models.DateTimeField(null=True, blank=True, help_text="When operator started prep")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="When operator marked done")

    wait_time_seconds = models.PositiveIntegerField(null=True, blank=True, help_text="Wait time until prep started")
    prep_time_seconds = models.PositiveIntegerField(null=True, blank=True, help_text="Prep time (started -> completed)")

    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["enqueued_at"]
        unique_together = [("station", "order")]
        indexes = [
            models.Index(fields=["station", "status"]),
            models.Index(fields=["station", "enqueued_at"]),
        ]

    def __str__(self):
        return f"Ticket Order#{self.order.display_number} @ {self.station.name} [{self.status}]"

    def start(self):
        """Mark as IN_PROGRESS. Does NOT save."""
        if self.status != KDSTicketStatus.WAITING:
            raise ValueError(f"Cannot start ticket in status {self.status}")
        now = timezone.now()
        self.status = KDSTicketStatus.IN_PROGRESS
        self.started_at = now
        if self.enqueued_at:
            self.wait_time_seconds = int((now - self.enqueued_at).total_seconds())

    def complete(self):
        """Mark as DONE. Does NOT save."""
        if self.status not in (KDSTicketStatus.WAITING, KDSTicketStatus.IN_PROGRESS):
            raise ValueError(f"Cannot complete ticket in status {self.status}")
        now = timezone.now()
        self.status = KDSTicketStatus.DONE
        self.completed_at = now
        if self.started_at:
            self.prep_time_seconds = int((now - self.started_at).total_seconds())
        if not self.wait_time_seconds and self.enqueued_at:
            self.wait_time_seconds = int((now - self.enqueued_at).total_seconds())
