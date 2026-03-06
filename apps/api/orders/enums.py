from django.db import models


class OrderStatus(models.TextChoices):
    PENDING = "PENDING", "Pendente"
    CONFIRMED = "CONFIRMED", "Confirmado"
    IN_PREPARATION = "IN_PREPARATION", "Em preparação"
    READY = "READY", "Pronto"
    DISPATCHED = "DISPATCHED", "Despachado"
    DELIVERED = "DELIVERED", "Entregue"
    CANCELLED = "CANCELLED", "Cancelado"


class OrderChannel(models.TextChoices):
    OWN = "OWN", "Canal próprio"
    IFOOD = "IFOOD", "iFood"
    NINETYNINE = "99FOOD", "99Food"
    OTHER = "OTHER", "Outro"


class OrderType(models.TextChoices):
    DELIVERY = "DELIVERY", "Entrega"
    TAKEOUT = "TAKEOUT", "Retirada"
    TABLE = "TABLE", "Mesa"


class PaymentMethod(models.TextChoices):
    CASH = "CASH", "Dinheiro"
    CARD_ON_DELIVERY = "CARD_ON_DELIVERY", "Cartão na entrega"
    PIX = "PIX", "PIX"
