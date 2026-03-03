from rest_framework_nested import routers

from .views import CatalogViewSet, CategoryViewSet, ProductChannelMapViewSet, ProductViewSet

router = routers.DefaultRouter()
router.register(r"catalogs", CatalogViewSet, basename="catalog")

catalogs_router = routers.NestedDefaultRouter(router, r"catalogs", lookup="catalog")
catalogs_router.register(r"categories", CategoryViewSet, basename="catalog-category")

categories_router = routers.NestedDefaultRouter(catalogs_router, r"categories", lookup="category")
categories_router.register(r"products", ProductViewSet, basename="category-product")

products_router = routers.NestedDefaultRouter(categories_router, r"products", lookup="product")
products_router.register(r"channel-maps", ProductChannelMapViewSet, basename="product-channelmap")

urlpatterns = router.urls + catalogs_router.urls + categories_router.urls + products_router.urls
