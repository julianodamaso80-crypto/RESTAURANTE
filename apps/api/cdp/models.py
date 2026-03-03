import uuid

from django.db import models
from django.utils import timezone


class IdentityType(models.TextChoices):
    PHONE = "PHONE", "Telefone"
    EMAIL = "EMAIL", "E-mail"
    CPF = "CPF", "CPF"
    IFOOD_ID = "IFOOD_ID", "iFood ID"
    FOOD99 = "99FOOD_ID", "99Food ID"
    EXTERNAL = "EXTERNAL", "Externo"


class ConsentChannel(models.TextChoices):
    WHATSAPP = "WHATSAPP", "WhatsApp"
    EMAIL = "EMAIL", "E-mail"
    SMS = "SMS", "SMS"
    PUSH = "PUSH", "Push notification"


class ConsentStatus(models.TextChoices):
    GRANTED = "GRANTED", "Consentiu"
    REVOKED = "REVOKED", "Revogou"


class CustomerEventType(models.TextChoices):
    ORDER_PLACED = "ORDER_PLACED", "Pedido realizado"
    ORDER_DELIVERED = "ORDER_DELIVERED", "Pedido entregue"
    ORDER_CANCELLED = "ORDER_CANCELLED", "Pedido cancelado"
    COUPON_USED = "COUPON_USED", "Cupom utilizado"
    CONSENT_GRANTED = "CONSENT_GRANTED", "Consentimento concedido"
    CONSENT_REVOKED = "CONSENT_REVOKED", "Consentimento revogado"
    PROFILE_UPDATED = "PROFILE_UPDATED", "Perfil atualizado"


class Customer(models.Model):
    """Perfil unificado do cliente por tenant.

    Um Customer representa a mesma pessoa em todas as stores da rede.
    Não é vinculado a uma Store específica — é do Tenant.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="customers")

    # Dados pessoais — todos opcionais (cliente pode ser anônimo inicialmente)
    name = models.CharField(max_length=255, blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")
    email = models.EmailField(blank=True, default="")

    # RFV — calculado assincronamente, nunca síncrono
    rfv_recency_days = models.PositiveIntegerField(null=True, blank=True, help_text="Dias desde último pedido")
    rfv_frequency = models.PositiveIntegerField(default=0, help_text="Total de pedidos entregues")
    rfv_monetary_cents = models.PositiveIntegerField(default=0, help_text="Valor total gasto em centavos")
    rfv_last_order_at = models.DateTimeField(null=True, blank=True)
    rfv_calculated_at = models.DateTimeField(null=True, blank=True, help_text="Última vez que RFV foi calculado")

    # Flags
    is_active = models.BooleanField(default=True)
    is_anonymous = models.BooleanField(default=False, help_text="Cliente sem identidade confirmada")

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "phone"]),
            models.Index(fields=["tenant", "email"]),
            models.Index(fields=["tenant", "rfv_recency_days"]),
        ]

    def __str__(self):
        identifier = self.phone or self.email or str(self.id)[:8]
        return f"Customer {identifier} (Tenant {self.tenant_id})"


class CustomerIdentity(models.Model):
    """Identidade externa do cliente (telefone verificado, email, iFood ID, etc.).

    Permite merge de perfis vindos de canais diferentes.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="identities")
    type = models.CharField(max_length=20, choices=IdentityType.choices)
    value = models.CharField(max_length=255, help_text="Valor da identidade (ex: +5511999999999)")
    is_verified = models.BooleanField(default=False)
    source = models.CharField(max_length=32, blank=True, default="", help_text="Origem (ifood, own, manual)")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("customer", "type", "value")]
        indexes = [
            models.Index(fields=["type", "value"]),
        ]

    def __str__(self):
        verified = "V" if self.is_verified else "?"
        return f"{self.type}:{self.value} [{verified}]"


class ConsentRecord(models.Model):
    """Registro auditável de consentimento LGPD.

    NUNCA deletar — apenas adicionar novos registros.
    O status atual é o registro mais recente por (customer, channel).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="consents")
    channel = models.CharField(max_length=20, choices=ConsentChannel.choices)
    status = models.CharField(max_length=10, choices=ConsentStatus.choices)

    # Contexto do consentimento
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    source = models.CharField(max_length=64, blank=True, default="", help_text="Onde foi coletado")
    legal_basis = models.CharField(max_length=255, blank=True, default="", help_text="Base legal LGPD")

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer", "channel", "-created_at"]),
        ]

    def __str__(self):
        return f"Consent {self.channel}:{self.status} — Customer {self.customer_id}"


class CustomerEvent(models.Model):
    """Log de eventos relevantes do ciclo de vida do cliente.

    Append-only — nunca editar ou deletar.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="events")
    store = models.ForeignKey(
        "tenants.Store", on_delete=models.SET_NULL, null=True, blank=True, related_name="customer_events"
    )
    event_type = models.CharField(max_length=30, choices=CustomerEventType.choices)
    payload = models.JSONField(default=dict, help_text="Dados do evento (order_id, coupon_code, etc.)")
    occurred_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["customer", "event_type"]),
            models.Index(fields=["customer", "occurred_at"]),
        ]

    def __str__(self):
        return f"Event {self.event_type} — Customer {self.customer_id}"
