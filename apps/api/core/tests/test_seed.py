import pytest
from django.core.management import call_command

from tenants.models import Store, Tenant


@pytest.mark.django_db
def test_seed_creates_tenants():
    call_command("seed")

    assert Tenant.objects.filter(name="Burguer Palace").exists()
    assert Tenant.objects.filter(name="Pizza Napoli").exists()


@pytest.mark.django_db
def test_seed_creates_stores():
    call_command("seed")

    bp = Tenant.objects.get(name="Burguer Palace")
    stores_bp = Store.objects.filter(company__tenant=bp)
    assert stores_bp.count() == 3

    np = Tenant.objects.get(name="Pizza Napoli")
    stores_np = Store.objects.filter(company__tenant=np)
    assert stores_np.count() == 1


@pytest.mark.django_db
def test_seed_creates_customers():
    from cdp.models import Customer

    call_command("seed")

    bp = Tenant.objects.get(name="Burguer Palace")
    customers = Customer.objects.filter(tenant=bp)
    assert customers.count() == 30


@pytest.mark.django_db
def test_seed_creates_orders():
    from orders.models import Order

    call_command("seed")

    bp = Tenant.objects.get(name="Burguer Palace")
    orders = Order.objects.filter(tenant=bp)
    assert orders.count() > 50


@pytest.mark.django_db
def test_seed_creates_catalog():
    from catalog.models import Catalog, Product

    call_command("seed")

    bp = Tenant.objects.get(name="Burguer Palace")
    assert Catalog.objects.filter(tenant=bp).exists()
    assert Product.objects.filter(category__catalog__tenant=bp).count() >= 10


@pytest.mark.django_db
def test_seed_creates_stock():
    from stock.models import StockAlert, StockItem, StockLevel

    call_command("seed")

    bp = Tenant.objects.get(name="Burguer Palace")
    store = Store.objects.get(company__tenant=bp, slug="paulista")
    items = StockItem.objects.filter(store=store)
    assert items.count() == 7

    # Saldos calculados
    assert StockLevel.objects.filter(stock_item__store=store).count() == 7

    # Alerta de catchup sache
    assert StockAlert.objects.filter(stock_item__name="Catchup sache", is_resolved=False).exists()


@pytest.mark.django_db
def test_seed_creates_kds_stations():
    from kds.models import KDSStation

    call_command("seed")

    bp = Tenant.objects.get(name="Burguer Palace")
    store = Store.objects.get(company__tenant=bp, slug="paulista")
    assert KDSStation.objects.filter(store=store).count() == 3


@pytest.mark.django_db
def test_seed_creates_crm_demo():
    from crm.models import Campaign, CustomerSegment, TenantBillingQuota

    call_command("seed")

    bp = Tenant.objects.get(name="Burguer Palace")
    assert CustomerSegment.objects.filter(tenant=bp).count() == 3
    assert Campaign.objects.filter(tenant=bp, name="Black Friday Burguer").exists()
    assert TenantBillingQuota.objects.filter(tenant=bp).exists()


@pytest.mark.django_db
def test_seed_rfv_calculated():
    from cdp.models import Customer

    call_command("seed")

    bp = Tenant.objects.get(name="Burguer Palace")
    # VIP customers should have rfv_frequency >= 10
    vip_count = Customer.objects.filter(tenant=bp, rfv_frequency__gte=10).count()
    assert vip_count >= 3


@pytest.mark.django_db
def test_seed_clear_and_reseed():
    call_command("seed")
    assert Tenant.objects.filter(name="Burguer Palace").exists()

    call_command("seed", clear=True)
    # Should still exist after re-seed
    assert Tenant.objects.filter(name="Burguer Palace").count() == 1
