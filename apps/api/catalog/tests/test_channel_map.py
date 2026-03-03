import pytest

from catalog.models import ChannelType, ProductChannelMap


@pytest.mark.django_db
def test_channel_map_stores_external_id(product_channel_map_factory):
    cmap = product_channel_map_factory(channel=ChannelType.IFOOD, external_id="ifood-abc-123")
    assert cmap.external_id == "ifood-abc-123"


@pytest.mark.django_db
def test_channel_map_price_override(product_factory, product_channel_map_factory):
    p = product_factory(price_cents=2000)
    cmap = product_channel_map_factory(product=p, channel=ChannelType.IFOOD, price_override_cents=2500)
    assert cmap.price_override_cents == 2500
    assert p.price_cents == 2000  # preço base não muda


@pytest.mark.django_db
def test_lookup_by_channel_external_id(product_channel_map_factory):
    cmap = product_channel_map_factory(channel=ChannelType.IFOOD, external_id="ext-xyz")
    found = ProductChannelMap.objects.get(channel=ChannelType.IFOOD, external_id="ext-xyz")
    assert found.id == cmap.id


@pytest.mark.django_db
def test_channel_map_default_values(product_channel_map_factory):
    cmap = product_channel_map_factory()
    assert cmap.is_active is True
    assert cmap.external_sku == ""
    assert cmap.price_override_cents is None


@pytest.mark.django_db
def test_orders_app_does_not_import_catalog():
    """Confirma que orders/ não depende de catalog/ (snapshot intencional)."""
    import inspect

    import orders.models as m

    source = inspect.getsource(m)
    # Check for actual imports, not comments mentioning catalog
    assert "from catalog" not in source
    assert "import catalog" not in source
