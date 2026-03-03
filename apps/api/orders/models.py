import uuid

from django.db import models
from django.utils import timezone

from tenants.models import Store, Tenant, User

from .enums import OrderChannel, OrderStatus, OrderType
from .fsm import transition


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name="orders")
    store = models.ForeignKey(Store, on_delete=models.PROTECT, related_name="orders")

    # Identification
    display_number = models.CharField(max_length=32, help_text="Number displayed to customer, e.g. #0042")
    channel = models.CharField(max_length=20, choices=OrderChannel.choices, default=OrderChannel.OWN)
    order_type = models.CharField(max_length=20, choices=OrderType.choices)
    external_id = models.CharField(max_length=128, blank=True, null=True, help_text="ID in the source marketplace")

    # State
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)

    # Values (in cents to avoid float)
    subtotal_cents = models.PositiveIntegerField(default=0)
    discount_cents = models.PositiveIntegerField(default=0)
    delivery_fee_cents = models.PositiveIntegerField(default=0)
    total_cents = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_orders"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "store", "status"]),
            models.Index(fields=["tenant", "external_id"]),
            models.Index(fields=["store", "created_at"]),
        ]

    def __str__(self):
        return f"Order {self.display_number} [{self.status}] - Store {self.store_id}"

    def transition_to(self, new_status: str):
        """Apply FSM state transition. Does NOT save."""
        transition(self, new_status)
        now = timezone.now()
        if new_status == OrderStatus.CONFIRMED:
            self.confirmed_at = now
        elif new_status == OrderStatus.DELIVERED:
            self.delivered_at = now
        elif new_status == OrderStatus.CANCELLED:
            self.cancelled_at = now


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")

    # Snapshot of product at order time (no FK to catalog — intentional)
    name = models.CharField(max_length=255)
    external_item_id = models.CharField(max_length=128, blank=True, null=True)
    quantity = models.PositiveSmallIntegerField()
    unit_price_cents = models.PositiveIntegerField()
    total_cents = models.PositiveIntegerField()
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.quantity}x {self.name} (Order {self.order_id})"


class IdempotencyKey(models.Model):
    """Ensures external events (future webhooks) don't create duplicate Orders.

    Lookup: tenant + key → order (if already processed).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="idempotency_keys")
    key = models.CharField(max_length=255, help_text="Unique key provided by caller (e.g. webhook event_id)")
    order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.SET_NULL, related_name="idempotency_keys")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("tenant", "key")]
        indexes = [
            models.Index(fields=["tenant", "key"]),
        ]

    def __str__(self):
        return f"IdempotencyKey {self.key} (Tenant {self.tenant_id})"
