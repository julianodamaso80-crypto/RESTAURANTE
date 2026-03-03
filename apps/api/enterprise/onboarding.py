import structlog
from django.utils import timezone

log = structlog.get_logger()

ONBOARDING_STEPS = [
    "copy_catalog",
    "copy_kds_stations",
    "copy_bom",
    "create_billing_quota",
    "create_store_override",
]


def run_onboarding(onboarding_id: str):
    """
    Executa o onboarding de uma nova store a partir do FranchiseTemplate.
    Idempotente: verifica steps_completed antes de cada step.
    """
    from .models import FranchiseeOnboarding, OnboardingStatus

    try:
        ob = FranchiseeOnboarding.objects.select_related("template__company", "store").get(id=onboarding_id)
    except FranchiseeOnboarding.DoesNotExist:
        log.error("onboarding_not_found", id=onboarding_id)
        return

    ob.status = OnboardingStatus.RUNNING
    ob.started_at = timezone.now()
    ob.save(update_fields=["status", "started_at"])

    steps_fn = {
        "copy_catalog": lambda: _copy_catalog(ob),
        "copy_kds_stations": lambda: _copy_kds_stations(ob),
        "copy_bom": lambda: _copy_bom(ob),
        "create_billing_quota": lambda: _create_billing_quota(ob),
        "create_store_override": lambda: _create_store_override(ob),
    }

    try:
        for step_name in ONBOARDING_STEPS:
            if step_name in ob.steps_completed:
                log.info("onboarding_step_skipped", step=step_name, store=ob.store.name)
                continue

            log.info("onboarding_step_start", step=step_name, store=ob.store.name)
            steps_fn[step_name]()
            ob.steps_completed.append(step_name)
            ob.save(update_fields=["steps_completed"])
            log.info("onboarding_step_done", step=step_name)

        ob.status = OnboardingStatus.DONE
        ob.completed_at = timezone.now()
        ob.save(update_fields=["status", "completed_at"])
        log.info("onboarding_completed", store=ob.store.name)

    except Exception as e:
        ob.status = OnboardingStatus.FAILED
        ob.error_detail = str(e)
        ob.save(update_fields=["status", "error_detail"])
        log.error("onboarding_failed", store=ob.store.name, error=str(e))
        raise


def _copy_catalog(ob):
    """
    Cria um Catalog para a store baseado no template_catalog da rede.
    Copia categorias e produtos (sem duplicar — get_or_create).
    """
    template_catalog = ob.template.template_catalog
    if not template_catalog:
        return

    from catalog.models import Catalog, CatalogStatus, Category, Product

    store_catalog, _created = Catalog.objects.get_or_create(
        store=ob.store,
        name=template_catalog.name,
        defaults={
            "tenant": ob.store.company.tenant,
            "company": ob.store.company,
            "status": CatalogStatus.ACTIVE,
            "channels": template_catalog.channels,
        },
    )

    for category in template_catalog.categories.filter(status=CatalogStatus.ACTIVE):
        store_cat, _ = Category.objects.get_or_create(
            catalog=store_catalog,
            name=category.name,
            defaults={
                "description": category.description,
                "status": category.status,
                "display_order": category.display_order,
            },
        )
        for product in category.products.filter(status=CatalogStatus.ACTIVE):
            Product.objects.get_or_create(
                category=store_cat,
                name=product.name,
                defaults={
                    "description": product.description,
                    "price_cents": product.price_cents,
                    "status": product.status,
                    "display_order": product.display_order,
                    "tags": product.tags,
                },
            )


def _copy_kds_stations(ob):
    """Cria estações KDS padrão da rede na nova store."""
    from kds.models import KDSStation

    for station_data in ob.template.default_kds_stations:
        KDSStation.objects.get_or_create(
            store=ob.store,
            name=station_data["name"],
            defaults={
                "category": station_data.get("category", "GENERAL"),
                "display_order": station_data.get("display_order", 0),
                "is_active": True,
            },
        )


def _copy_bom(ob):
    """
    Copia BOM do template para os produtos da nova store.
    Busca produtos pelo nome (match entre template e store).
    """
    from catalog.models import Product
    from stock.models import BillOfMaterials, StockItem

    if not ob.template.template_catalog:
        return

    template_products = Product.objects.filter(
        category__catalog=ob.template.template_catalog
    ).prefetch_related("bom_items__stock_item")

    for template_product in template_products:
        try:
            store_product = Product.objects.get(
                category__catalog__store=ob.store,
                name=template_product.name,
            )
        except Product.DoesNotExist:
            continue

        for bom in template_product.bom_items.filter(is_active=True):
            store_stock_item, _ = StockItem.objects.get_or_create(
                store=ob.store,
                name=bom.stock_item.name,
                defaults={
                    "unit": bom.stock_item.unit,
                    "minimum_stock": bom.stock_item.minimum_stock,
                },
            )
            BillOfMaterials.objects.get_or_create(
                product=store_product,
                stock_item=store_stock_item,
                defaults={"quantity_per_unit": bom.quantity_per_unit},
            )


def _create_billing_quota(ob):
    """Cria TenantBillingQuota para o tenant da nova store."""
    from crm.models import TenantBillingQuota

    TenantBillingQuota.objects.get_or_create(
        tenant=ob.store.company.tenant,
        defaults={"max_contacts": 1000, "current_period_contacts": 0},
    )


def _create_store_override(ob):
    """Cria StoreOverride vazio (store herda tudo do template por padrão)."""
    from .models import StoreOverride

    StoreOverride.objects.get_or_create(
        store=ob.store,
        defaults={"template": ob.template},
    )
