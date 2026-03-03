import uuid

from django.db import models
from django.utils import timezone


class CatalogStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Ativo"
    INACTIVE = "INACTIVE", "Inativo"
    DRAFT = "DRAFT", "Rascunho"


class ChannelType(models.TextChoices):
    OWN = "OWN", "Canal próprio"
    IFOOD = "IFOOD", "iFood"
    FOOD99 = "99FOOD", "99Food"
    ALL = "ALL", "Todos os canais"


class WeekDay(models.IntegerChoices):
    MONDAY = 0, "Segunda"
    TUESDAY = 1, "Terça"
    WEDNESDAY = 2, "Quarta"
    THURSDAY = 3, "Quinta"
    FRIDAY = 4, "Sexta"
    SATURDAY = 5, "Sábado"
    SUNDAY = 6, "Domingo"


class Catalog(models.Model):
    """Cardápio. Uma store pode ter múltiplos (ex: Almoço, Jantar, Delivery).

    Pode ser definido no nível company (compartilhado) ou store (local).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="catalogs")
    company = models.ForeignKey(
        "tenants.Company", on_delete=models.CASCADE, related_name="catalogs", null=True, blank=True
    )
    store = models.ForeignKey(
        "tenants.Store",
        on_delete=models.CASCADE,
        related_name="catalogs",
        null=True,
        blank=True,
        help_text="Se null, catálogo é compartilhado para todas as stores da company",
    )
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=CatalogStatus.choices, default=CatalogStatus.DRAFT)
    channels = models.JSONField(default=list, help_text="Canais onde este catálogo é exibido. Vazio = todos.")
    display_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        scope = f"Store {self.store_id}" if self.store_id else f"Company {self.company_id}"
        return f"{self.name} [{self.status}] — {scope}"


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    catalog = models.ForeignKey(Catalog, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    image_url = models.URLField(blank=True, default="")
    status = models.CharField(max_length=10, choices=CatalogStatus.choices, default=CatalogStatus.ACTIVE)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.name} (Catalog {self.catalog_id})"


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    image_url = models.URLField(blank=True, default="")

    # Preço base em centavos
    price_cents = models.PositiveIntegerField()

    status = models.CharField(max_length=10, choices=CatalogStatus.choices, default=CatalogStatus.ACTIVE)
    display_order = models.PositiveSmallIntegerField(default=0)

    # Tags livres para filtros (ex: ["vegano", "sem-gluten"])
    tags = models.JSONField(default=list, blank=True)

    # Metadados nutricionais opcionais
    serving_size = models.CharField(max_length=50, blank=True, default="")
    calories = models.PositiveSmallIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.name} — R${self.price_cents / 100:.2f}"


class ModifierGroup(models.Model):
    """Grupo de modificadores vinculado a um produto.

    Ex: "Ponto da carne", "Adicionais", "Remover ingredientes"
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="modifier_groups")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")

    min_choices = models.PositiveSmallIntegerField(default=0, help_text="Mínimo obrigatório (0 = opcional)")
    max_choices = models.PositiveSmallIntegerField(default=1, help_text="Máximo permitido")

    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return f"{self.name} (min={self.min_choices}, max={self.max_choices})"


class ModifierOption(models.Model):
    """Opção dentro de um grupo de modificadores.

    Ex: "Mal passado", "Ao ponto", "Bem passado"
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(ModifierGroup, on_delete=models.CASCADE, related_name="options")
    name = models.CharField(max_length=100)
    price_delta_cents = models.IntegerField(default=0, help_text="Acréscimo (+) ou desconto (-) em centavos")
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        delta = f"+R${self.price_delta_cents / 100:.2f}" if self.price_delta_cents > 0 else ""
        return f"{self.name} {delta}"


class ProductChannelMap(models.Model):
    """Mapeamento do produto interno para ID externo em cada canal (iFood, etc.).

    Permite que o mesmo produto tenha IDs diferentes em cada marketplace.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="channel_maps")
    channel = models.CharField(max_length=20, choices=ChannelType.choices)
    external_id = models.CharField(max_length=255, help_text="ID do produto no canal externo")
    external_sku = models.CharField(max_length=255, blank=True, default="")

    # Override de preço por canal (null = usa price_cents do produto)
    price_override_cents = models.PositiveIntegerField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("product", "channel")]
        indexes = [
            models.Index(fields=["channel", "external_id"]),
        ]

    def __str__(self):
        return f"{self.product.name} @ {self.channel} → {self.external_id}"


class ProductAvailability(models.Model):
    """Janela de disponibilidade de um produto por dia da semana e horário.

    Um produto sem registros = disponível sempre.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="availability_windows")
    week_day = models.IntegerField(choices=WeekDay.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ["week_day", "start_time"]
        unique_together = [("product", "week_day", "start_time")]

    def __str__(self):
        return f"{self.product.name} — {WeekDay(self.week_day).label} {self.start_time}–{self.end_time}"

    def is_available_now(self) -> bool:
        from django.utils import timezone as tz

        now = tz.localtime()
        if now.weekday() != self.week_day:
            return False
        return self.start_time <= now.time() <= self.end_time
