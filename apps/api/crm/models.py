import uuid

from django.db import models
from django.utils import timezone


class SegmentCriteria(models.TextChoices):
    ALL_CUSTOMERS = "ALL_CUSTOMERS", "Todos os clientes"
    RFV_RECENCY_LTE = "RFV_RECENCY_LTE", "Recência ≤ X dias"
    RFV_FREQUENCY_GTE = "RFV_FREQUENCY_GTE", "Frequência ≥ X pedidos"
    RFV_MONETARY_GTE = "RFV_MONETARY_GTE", "Valor total ≥ X centavos"
    HAS_CONSENT = "HAS_CONSENT", "Tem consentimento no canal"
    NO_ORDER_SINCE_DAYS = "NO_ORDER_SINCE_DAYS", "Sem pedido há ≥ X dias (win-back)"


class CampaignStatus(models.TextChoices):
    DRAFT = "DRAFT", "Rascunho"
    SCHEDULED = "SCHEDULED", "Agendada"
    RUNNING = "RUNNING", "Rodando"
    COMPLETED = "COMPLETED", "Concluída"
    CANCELLED = "CANCELLED", "Cancelada"


class RecipientStatus(models.TextChoices):
    PENDING = "PENDING", "Pendente"
    SENT = "SENT", "Enviado"
    DELIVERED = "DELIVERED", "Entregue"
    FAILED = "FAILED", "Falhou"
    OPTED_OUT = "OPTED_OUT", "Sem consentimento"


class CustomerSegment(models.Model):
    """Segmento dinâmico de clientes.

    Critérios são avaliados em runtime (não pré-computados).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="segments")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")

    # Critérios como JSON — lista de {criteria: str, value: any}
    # Ex: [{"criteria": "RFV_RECENCY_LTE", "value": 30}, {"criteria": "HAS_CONSENT", "value": "WHATSAPP"}]
    criteria = models.JSONField(default=list)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"Segment: {self.name} (Tenant {self.tenant_id})"


class CampaignTemplate(models.Model):
    """Template de mensagem reutilizável por campanha."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="campaign_templates")
    name = models.CharField(max_length=100)
    channel = models.CharField(max_length=20)  # ConsentChannel values
    subject = models.CharField(max_length=255, blank=True, default="", help_text="Assunto (email)")
    body = models.TextField(help_text="Corpo com variáveis {{name}}, {{store_name}}, {{coupon_code}}")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Template: {self.name} [{self.channel}]"


class Campaign(models.Model):
    """Campanha de CRM — une segmento + template + store.

    Uma campanha pode ter múltiplas execuções (runs).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="campaigns")
    store = models.ForeignKey(
        "tenants.Store",
        on_delete=models.CASCADE,
        related_name="campaigns",
        null=True,
        blank=True,
        help_text="Null = campanha de rede (todas as stores)",
    )
    name = models.CharField(max_length=100)
    segment = models.ForeignKey(CustomerSegment, on_delete=models.PROTECT, related_name="campaigns")
    template = models.ForeignKey(CampaignTemplate, on_delete=models.PROTECT, related_name="campaigns")
    status = models.CharField(max_length=15, choices=CampaignStatus.choices, default=CampaignStatus.DRAFT)
    scheduled_at = models.DateTimeField(null=True, blank=True, help_text="Quando disparar (null = manual)")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Campaign: {self.name} [{self.status}]"


class CampaignRun(models.Model):
    """Instância de execução de uma campanha.

    Uma Campaign pode ter várias CampaignRuns (ex: mensal).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="runs")
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_recipients = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    delivered_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    opted_out_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=15, choices=CampaignStatus.choices, default=CampaignStatus.RUNNING)
    error_detail = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"Run #{self.id} — {self.campaign.name} [{self.status}]"


class CampaignRecipient(models.Model):
    """Rastreamento por destinatário em uma CampaignRun.

    Um registro por (run, customer).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run = models.ForeignKey(CampaignRun, on_delete=models.CASCADE, related_name="recipients")
    customer = models.ForeignKey("cdp.Customer", on_delete=models.CASCADE, related_name="campaign_recipients")
    status = models.CharField(max_length=15, choices=RecipientStatus.choices, default=RecipientStatus.PENDING)
    channel = models.CharField(max_length=20)
    destination = models.CharField(max_length=255, blank=True, default="", help_text="Telefone/email destino")
    sent_at = models.DateTimeField(null=True, blank=True)
    error_detail = models.TextField(blank=True, default="")

    class Meta:
        unique_together = [("run", "customer")]
        ordering = ["id"]

    def __str__(self):
        return f"Recipient {self.customer_id} [{self.status}]"


class TenantBillingQuota(models.Model):
    """Teto de contatos por tenant por período.

    Diferencial vs Repediu: sem upgrade automático silencioso.
    Alerta em 80%, BLOQUEIO em 100% com mensagem clara.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField("tenants.Tenant", on_delete=models.CASCADE, related_name="billing_quota")
    max_contacts = models.PositiveIntegerField(default=1000, help_text="Teto do plano atual")
    current_period_contacts = models.PositiveIntegerField(default=0, help_text="Contatos usados no período atual")
    period_start = models.DateField(default=timezone.now)
    alert_sent_at_80 = models.DateTimeField(null=True, blank=True)
    blocked_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def usage_pct(self) -> float:
        if self.max_contacts == 0:
            return 100.0
        return (self.current_period_contacts / self.max_contacts) * 100

    @property
    def is_blocked(self) -> bool:
        return self.current_period_contacts >= self.max_contacts

    @property
    def is_near_limit(self) -> bool:
        return self.usage_pct >= 80.0

    def __str__(self):
        return f"Quota Tenant {self.tenant_id}: {self.current_period_contacts}/{self.max_contacts}"
