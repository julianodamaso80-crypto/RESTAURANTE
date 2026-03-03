import pytest
from django.db import IntegrityError

from catalog.models import CatalogStatus


@pytest.mark.django_db
def test_product_creation(product_factory):
    p = product_factory()
    assert p.pk is not None
    assert p.price_cents > 0


@pytest.mark.django_db
def test_modifier_group_constraints(modifier_group_factory):
    mg = modifier_group_factory(min_choices=1, max_choices=3)
    assert mg.min_choices == 1
    assert mg.max_choices == 3


@pytest.mark.django_db
def test_channel_map_unique_per_channel(product_channel_map_factory, product_factory):
    p = product_factory()
    product_channel_map_factory(product=p, channel="IFOOD")
    with pytest.raises(IntegrityError):
        product_channel_map_factory(product=p, channel="IFOOD")


@pytest.mark.django_db
def test_catalog_hierarchy(catalog_factory, category_factory, product_factory):
    catalog = catalog_factory()
    category = category_factory(catalog=catalog)
    product = product_factory(category=category)
    assert product.category.catalog == catalog


@pytest.mark.django_db
def test_catalog_str(catalog_factory):
    catalog = catalog_factory(name="Almoço", status=CatalogStatus.ACTIVE)
    assert "Almoço" in str(catalog)
    assert "ACTIVE" in str(catalog)


@pytest.mark.django_db
def test_product_str(product_factory):
    p = product_factory(name="X-Burger", price_cents=1500)
    assert "X-Burger" in str(p)
    assert "15.00" in str(p)


@pytest.mark.django_db
def test_modifier_group_str(modifier_group_factory):
    mg = modifier_group_factory(name="Ponto da carne", min_choices=1, max_choices=1)
    s = str(mg)
    assert "Ponto da carne" in s
    assert "min=1" in s


@pytest.mark.django_db
def test_modifier_option_str(modifier_option_factory):
    opt = modifier_option_factory(name="Bem passado", price_delta_cents=300)
    s = str(opt)
    assert "Bem passado" in s
    assert "3.00" in s


@pytest.mark.django_db
def test_category_str(category_factory):
    cat = category_factory(name="Lanches")
    assert "Lanches" in str(cat)


@pytest.mark.django_db
def test_product_channel_map_str(product_channel_map_factory, product_factory):
    p = product_factory(name="Hambúrguer")
    cmap = product_channel_map_factory(product=p, channel="IFOOD", external_id="ext-123")
    s = str(cmap)
    assert "Hambúrguer" in s
    assert "IFOOD" in s
    assert "ext-123" in s
