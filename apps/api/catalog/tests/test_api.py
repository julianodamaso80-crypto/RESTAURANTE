import pytest

from catalog.models import CatalogStatus


@pytest.mark.django_db
def test_catalog_list_requires_auth(api_client):
    response = api_client.get("/api/v1/catalogs/")
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_catalog_list_returns_scoped(auth_client, catalog_factory, other_store):
    my_catalog = catalog_factory()
    other_catalog = catalog_factory(store=other_store, company=other_store.company, tenant=other_store.company.tenant)
    response = auth_client.get("/api/v1/catalogs/")
    assert response.status_code == 200
    ids = [c["id"] for c in response.json()]
    assert str(my_catalog.id) in ids
    assert str(other_catalog.id) not in ids


@pytest.mark.django_db
def test_create_catalog(auth_client):
    response = auth_client.post(
        "/api/v1/catalogs/",
        {
            "name": "Cardápio Delivery",
            "status": "DRAFT",
            "channels": ["IFOOD", "OWN"],
            "display_order": 0,
        },
        format="json",
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Cardápio Delivery"
    assert data["status"] == "DRAFT"
    assert data["channels"] == ["IFOOD", "OWN"]


@pytest.mark.django_db
def test_catalog_retrieve(auth_client, catalog_factory):
    catalog = catalog_factory()
    response = auth_client.get(f"/api/v1/catalogs/{catalog.id}/")
    assert response.status_code == 200
    assert response.json()["name"] == catalog.name


@pytest.mark.django_db
def test_catalog_update(auth_client, catalog_factory):
    catalog = catalog_factory(name="Antigo")
    response = auth_client.patch(
        f"/api/v1/catalogs/{catalog.id}/",
        {"name": "Novo"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Novo"


@pytest.mark.django_db
def test_catalog_delete(auth_client, catalog_factory):
    catalog = catalog_factory()
    response = auth_client.delete(f"/api/v1/catalogs/{catalog.id}/")
    assert response.status_code == 204


@pytest.mark.django_db
def test_catalog_public_endpoint_no_auth(api_client, catalog_factory):
    catalog = catalog_factory(status=CatalogStatus.ACTIVE)
    response = api_client.get(f"/api/v1/catalogs/{catalog.id}/public/")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(catalog.id)
    assert data["name"] == catalog.name


@pytest.mark.django_db
def test_catalog_public_inactive_returns_404(api_client, catalog_factory):
    catalog = catalog_factory(status=CatalogStatus.INACTIVE)
    response = api_client.get(f"/api/v1/catalogs/{catalog.id}/public/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_catalog_public_shows_active_products(api_client, catalog_factory, store):
    from catalog.tests.factories import CategoryFactory, ProductFactory

    catalog = catalog_factory(status=CatalogStatus.ACTIVE)
    cat = CategoryFactory(catalog=catalog, status=CatalogStatus.ACTIVE)
    ProductFactory(category=cat, name="Ativo", status=CatalogStatus.ACTIVE)
    ProductFactory(category=cat, name="Inativo", status=CatalogStatus.INACTIVE)

    response = api_client.get(f"/api/v1/catalogs/{catalog.id}/public/")
    assert response.status_code == 200
    products = response.json()["categories"][0]["products"]
    names = [p["name"] for p in products]
    assert "Ativo" in names
    assert "Inativo" not in names


# --- Category nested endpoints ---


@pytest.mark.django_db
def test_category_list(auth_client, catalog_factory):
    from catalog.tests.factories import CategoryFactory

    catalog = catalog_factory()
    CategoryFactory(catalog=catalog, name="Lanches")
    CategoryFactory(catalog=catalog, name="Bebidas")

    response = auth_client.get(f"/api/v1/catalogs/{catalog.id}/categories/")
    assert response.status_code == 200
    names = [c["name"] for c in response.json()]
    assert "Lanches" in names
    assert "Bebidas" in names


@pytest.mark.django_db
def test_category_create(auth_client, catalog_factory):
    catalog = catalog_factory()
    response = auth_client.post(
        f"/api/v1/catalogs/{catalog.id}/categories/",
        {"name": "Sobremesas", "status": "ACTIVE", "display_order": 0},
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Sobremesas"


# --- Product nested endpoints ---


@pytest.mark.django_db
def test_product_list(auth_client, catalog_factory):
    from catalog.tests.factories import CategoryFactory, ProductFactory

    catalog = catalog_factory()
    cat = CategoryFactory(catalog=catalog)
    ProductFactory(category=cat, name="X-Burger")
    ProductFactory(category=cat, name="X-Salada")

    response = auth_client.get(f"/api/v1/catalogs/{catalog.id}/categories/{cat.id}/products/")
    assert response.status_code == 200
    names = [p["name"] for p in response.json()]
    assert "X-Burger" in names
    assert "X-Salada" in names


@pytest.mark.django_db
def test_product_create(auth_client, catalog_factory):
    from catalog.tests.factories import CategoryFactory

    catalog = catalog_factory()
    cat = CategoryFactory(catalog=catalog)
    response = auth_client.post(
        f"/api/v1/catalogs/{catalog.id}/categories/{cat.id}/products/",
        {"name": "Novo Produto", "price_cents": 1500, "status": "ACTIVE", "display_order": 0},
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Novo Produto"
    assert response.json()["price_cents"] == 1500


@pytest.mark.django_db
def test_product_detail_includes_modifiers(auth_client, catalog_factory):
    from catalog.tests.factories import CategoryFactory, ModifierGroupFactory, ModifierOptionFactory, ProductFactory

    catalog = catalog_factory()
    cat = CategoryFactory(catalog=catalog)
    product = ProductFactory(category=cat)
    mg = ModifierGroupFactory(product=product, name="Ponto da carne")
    ModifierOptionFactory(group=mg, name="Mal passado")
    ModifierOptionFactory(group=mg, name="Bem passado")

    response = auth_client.get(f"/api/v1/catalogs/{catalog.id}/categories/{cat.id}/products/{product.id}/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["modifier_groups"]) == 1
    assert data["modifier_groups"][0]["name"] == "Ponto da carne"
    assert len(data["modifier_groups"][0]["options"]) == 2


@pytest.mark.django_db
def test_product_available_endpoint(auth_client, catalog_factory):
    from catalog.tests.factories import CategoryFactory, ProductFactory

    catalog = catalog_factory()
    cat = CategoryFactory(catalog=catalog)
    ProductFactory(category=cat, status=CatalogStatus.ACTIVE)

    response = auth_client.get(f"/api/v1/catalogs/{catalog.id}/categories/{cat.id}/products/available/")
    assert response.status_code == 200


# --- Channel map nested endpoints ---


@pytest.mark.django_db
def test_channel_map_create(auth_client, catalog_factory):
    from catalog.tests.factories import CategoryFactory, ProductFactory

    catalog = catalog_factory()
    cat = CategoryFactory(catalog=catalog)
    product = ProductFactory(category=cat)

    response = auth_client.post(
        f"/api/v1/catalogs/{catalog.id}/categories/{cat.id}/products/{product.id}/channel-maps/",
        {"channel": "IFOOD", "external_id": "ifood-abc-123", "is_active": True},
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["external_id"] == "ifood-abc-123"


@pytest.mark.django_db
def test_channel_map_list(auth_client, catalog_factory):
    from catalog.tests.factories import CategoryFactory, ProductChannelMapFactory, ProductFactory

    catalog = catalog_factory()
    cat = CategoryFactory(catalog=catalog)
    product = ProductFactory(category=cat)
    ProductChannelMapFactory(product=product, channel="IFOOD", external_id="ext-1")

    response = auth_client.get(
        f"/api/v1/catalogs/{catalog.id}/categories/{cat.id}/products/{product.id}/channel-maps/"
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["external_id"] == "ext-1"
