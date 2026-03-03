import uuid

from django.db import models
from django.utils import timezone


class OnboardingStatus(models.TextChoices):
    PENDING = "PENDING", "Pendente"
    RUNNING = "RUNNING", "Executando"
    DONE = "DONE", "Concluído"
    FAILED = "FAILED", "Falhou"


class ReportPeriod(models.TextChoices):
    DAILY = "DAILY", "Diário"
    WEEKLY = "WEEKLY", "Semanal"
    MONTHLY = "MONTHLY", "Mensal"


class NetworkAlertType(models.TextChoices):
    STOCK_CRITICAL = "STOCK_CRITICAL", "Estoque crítico"
    RFV_DROP = "RFV_DROP", "Queda de frequência"
    KDS_BACKLOG = "KDS_BACKLOG", "Fila KDS acumulada"


class FranchiseTemplate(models.Model):
    """
    Modelo padrão da rede. Definido no nível Company.
    Cada nova store criada a partir deste template herda:
    - Catálogo base
    - Estações KDS padrão
    - Fichas técnicas (BOM) padrão
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.OneToOneField("tenants.Company", on_delete=models.CASCADE, related_name="franchise_template")
    name = models.CharField(max_length=100)
    template_catalog = models.ForeignKey(
        "catalog.Catalog", on_delete=models.SET_NULL, null=True, blank=True, related_name="franchise_templates"
    )
    # KDS padrão: JSON com lista de {name, category, display_order}
    default_kds_stations = models.JSONField(
        default=list, help_text='[{"name": "Chapa", "category": "GRILL", "display_order": 1}]'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Template: {self.name} ({self.company.name})"


class StoreOverride(models.Model):
    """
    Override granular de uma store em relação ao template da rede.
    Store herda tudo do FranchiseTemplate e sobrescreve apenas o necessário.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store = models.OneToOneField("tenants.Store", on_delete=models.CASCADE, related_name="franchise_override")
    template = models.ForeignKey(FranchiseTemplate, on_delete=models.CASCADE, related_name="store_overrides")

    # Overrides como JSON para flexibilidade máxima
    product_price_overrides = models.JSONField(default=dict, help_text='{"<product_uuid>": 3200}')
    product_status_overrides = models.JSONField(default=dict, help_text='{"<product_uuid>": "INACTIVE"}')
    bom_overrides = models.JSONField(default=dict, help_text='{"<bom_uuid>": "0.150"}')

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Override: {self.store.name} ← {self.template.name}"

    def get_product_price(self, product) -> int:
        """Retorna preço do produto com override aplicado."""
        override = self.product_price_overrides.get(str(product.id))
        return int(override) if override is not None else product.price_cents

    def is_product_active(self, product) -> bool:
        """Verifica se produto está ativo nesta store."""
        override = self.product_status_overrides.get(str(product.id))
        if override is not None:
            return override == "ACTIVE"
        from catalog.models import CatalogStatus

        return product.status == CatalogStatus.ACTIVE


class FranchiseeOnboarding(models.Model):
    """
    Provisionamento automático de nova store a partir do FranchiseTemplate.
    Idempotente: pode rodar múltiplas vezes sem duplicar dados.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(FranchiseTemplate, on_delete=models.CASCADE, related_name="onboardings")
    store = models.ForeignKey("tenants.Store", on_delete=models.CASCADE, related_name="onboarding")
    status = models.CharField(max_length=10, choices=OnboardingStatus.choices, default=OnboardingStatus.PENDING)
    steps_completed = models.JSONField(
        default=list,
        help_text='["copy_catalog", "copy_kds_stations", "copy_bom", "create_billing_quota", "create_store_override"]',
    )
    error_detail = models.TextField(blank=True, default="")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("template", "store")]

    def __str__(self):
        return f"Onboarding: {self.store.name} [{self.status}]"


class NetworkReport(models.Model):
    """
    Relatório consolidado da rede por período.
    Gerado assincronamente via Celery.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey("tenants.Company", on_delete=models.CASCADE, related_name="network_reports")
    period = models.CharField(max_length=10, choices=ReportPeriod.choices)
    date_from = models.DateField()
    date_to = models.DateField()
    data = models.JSONField(
        default=dict, help_text="Métricas consolidadas por store: orders, revenue, rfv, stock_alerts"
    )
    generated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-date_from"]
        unique_together = [("company", "period", "date_from")]

    def __str__(self):
        return f"NetworkReport {self.period} {self.date_from} — {self.company.name}"


class NetworkAlert(models.Model):
    """
    Alerta consolidado da rede.
    Criado quando alguma store tem situação crítica.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey("tenants.Company", on_delete=models.CASCADE, related_name="network_alerts")
    store = models.ForeignKey("tenants.Store", on_delete=models.CASCADE, related_name="network_alerts")
    alert_type = models.CharField(max_length=20, choices=NetworkAlertType.choices)
    payload = models.JSONField(default=dict, help_text="Dados do alerta")
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"NetworkAlert {self.alert_type} — {self.store.name}"
