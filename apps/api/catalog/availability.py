from django.db.models import Q
from django.utils import timezone as tz

from .models import CatalogStatus, Product, ProductAvailability


def is_product_available(product: Product, check_time=None) -> bool:
    """Verifica se um produto está disponível agora (ou no check_time dado).

    Regras:
    1. Produto deve estar ACTIVE
    2. Se não tem janelas de disponibilidade → disponível sempre
    3. Se tem janelas → deve ter pelo menos uma janela válida para o momento
    """
    if product.status != CatalogStatus.ACTIVE:
        return False

    windows = list(ProductAvailability.objects.filter(product=product))

    if not windows:
        return True  # sem restrição de horário

    now = check_time or tz.localtime()
    current_weekday = now.weekday()
    current_time = now.time()

    for window in windows:
        if window.week_day == current_weekday:
            if window.start_time <= current_time <= window.end_time:
                return True

    return False


def get_available_products_for_store(store, channel: str = None, check_time=None):
    """Retorna queryset de produtos disponíveis para uma store, opcionalmente filtrado por canal.

    Inclui produtos dos catálogos ativos da store e da sua company.
    """
    catalog_filter = Q(category__catalog__store=store) | Q(category__catalog__company=store.company)

    qs = (
        Product.objects.filter(
            catalog_filter,
            status=CatalogStatus.ACTIVE,
            category__status=CatalogStatus.ACTIVE,
            category__catalog__status=CatalogStatus.ACTIVE,
        )
        .select_related("category__catalog")
        .prefetch_related(
            "modifier_groups__options",
            "channel_maps",
            "availability_windows",
        )
        .distinct()
    )

    if channel and channel != "ALL":
        qs = qs.filter(Q(channel_maps__isnull=True) | Q(channel_maps__channel=channel, channel_maps__is_active=True))

    return qs
