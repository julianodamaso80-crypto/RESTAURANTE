import uuid

from django.db import models
from django.utils import timezone


class StockUnit(models.TextChoices):
    KG = "kg", "Quilograma"
    G = "g", "Grama"
    L = "L", "Litro"
    ML = "mL", "Mililitro"
    UN = "un", "Unidade"
    CX = "cx", "Caixa"
    PCT = "pct", "Pacote"


class MovementType(models.TextChoices):
    ENTRADA = "ENTRADA", "Entrada"
    SAIDA = "SAIDA", "Saída"
    AJUSTE = "AJUSTE", "Ajuste"
    PERDA = "PERDA", "Perda/Desperdício"
    INVENTARIO = "INVENTARIO", "Inventário"


class StockItem(models.Model):
    """Item de estoque: ingrediente, insumo ou embalagem.

    Vinculado à store (cada store tem seu próprio estoque).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store = models.ForeignKey("tenants.Store", on_delete=models.CASCADE, related_name="stock_items")
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=5, choices=StockUnit.choices, default=StockUnit.UN)
    minimum_stock = models.DecimalField(
        max_digits=10, decimal_places=3, default=0, help_text="Quantidade mínima para alerta"
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("store", "name")]

    def __str__(self):
        return f"{self.name} ({self.unit}) — Store {self.store_id}"


class StockMovement(models.Model):
    """Registro imutável de toda movimentação de estoque.

    Append-only: nunca editar ou deletar.
    quantidade positiva = entrada, negativa = saída.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name="movements")
    store = models.ForeignKey("tenants.Store", on_delete=models.CASCADE, related_name="stock_movements")
    type = models.CharField(max_length=15, choices=MovementType.choices)
    quantity = models.DecimalField(max_digits=10, decimal_places=3, help_text="Positivo=entrada, Negativo=saída")
    notes = models.TextField(blank=True, default="")

    # Referência opcional (order_id, NF, etc.)
    reference_type = models.CharField(max_length=50, blank=True, default="")
    reference_id = models.CharField(max_length=255, blank=True, default="")

    occurred_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        "tenants.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="stock_movements"
    )

    class Meta:
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["stock_item", "occurred_at"]),
            models.Index(fields=["store", "type"]),
            models.Index(fields=["reference_type", "reference_id"]),
        ]

    def __str__(self):
        sign = "+" if self.quantity > 0 else ""
        return f"{self.type} {sign}{self.quantity} {self.stock_item.unit} — {self.stock_item.name}"


class StockLevel(models.Model):
    """Saldo atual desnormalizado por item.

    Recalculado assincronamente após cada movimento.
    NÃO é a fonte da verdade — a fonte é StockMovement.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stock_item = models.OneToOneField(StockItem, on_delete=models.CASCADE, related_name="level")
    current_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    is_below_minimum = models.BooleanField(default=False)
    last_movement_at = models.DateTimeField(null=True, blank=True)
    calculated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.stock_item.name}: {self.current_quantity} {self.stock_item.unit}"


class StockAlert(models.Model):
    """Alerta gerado quando saldo < mínimo.

    Append-only: cada vez que o estoque ficar abaixo do mínimo, cria alerta.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name="alerts")
    store = models.ForeignKey("tenants.Store", on_delete=models.CASCADE, related_name="stock_alerts")
    current_qty = models.DecimalField(max_digits=10, decimal_places=3)
    minimum_qty = models.DecimalField(max_digits=10, decimal_places=3)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Alert: {self.stock_item.name} {self.current_qty}/{self.minimum_qty}"


class BillOfMaterials(models.Model):
    """Ficha técnica: quanto de cada StockItem um Product consome por unidade vendida.

    Liga catalog.Product → stock.StockItem.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="bom_items")
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name="bom_items")
    quantity_per_unit = models.DecimalField(
        max_digits=10, decimal_places=3, help_text="Quantidade consumida por unidade do produto"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("product", "stock_item")]

    def __str__(self):
        return f"{self.product.name} → {self.quantity_per_unit} {self.stock_item.unit} de {self.stock_item.name}"
