import structlog
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .availability import get_available_products_for_store
from .models import Catalog, CatalogStatus, Category, Product, ProductChannelMap
from .serializers import (
    CatalogPublicSerializer,
    CatalogSerializer,
    CategorySerializer,
    ProductChannelMapSerializer,
    ProductListSerializer,
    ProductSerializer,
)

log = structlog.get_logger()


class CatalogViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        if self.action == "public":
            return CatalogPublicSerializer
        return CatalogSerializer

    def get_queryset(self):
        store = self.request.scope_store
        if store is None:
            return Catalog.objects.none()
        return Catalog.objects.filter(
            Q(store=store) | Q(company=store.company, store__isnull=True)
        ).prefetch_related("categories__products")

    def perform_create(self, serializer):
        store = self.request.scope_store
        serializer.save(tenant=store.company.tenant, company=store.company, store=store)

    @action(detail=True, methods=["get"], url_path="public", permission_classes=[AllowAny])
    def public(self, request, pk=None):
        """Catálogo público de uma store. Usado pelo canal próprio e integrações.

        Não requer autenticação. Filtra produtos/categorias inativos.
        """
        try:
            catalog = Catalog.objects.prefetch_related(
                "categories__products__modifier_groups__options",
            ).get(pk=pk)
        except Catalog.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if catalog.status != CatalogStatus.ACTIVE:
            return Response({"detail": "Catalog not available."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CatalogPublicSerializer(catalog)
        return Response(serializer.data)


class CategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CategorySerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        catalog_id = self.kwargs.get("catalog_pk")
        store = self.request.scope_store
        if store is None:
            return Category.objects.none()
        return Category.objects.filter(
            catalog__id=catalog_id,
            catalog__store=store,
        ).prefetch_related("products")

    def perform_create(self, serializer):
        catalog = Catalog.objects.get(
            id=self.kwargs["catalog_pk"],
            store=self.request.scope_store,
        )
        serializer.save(catalog=catalog)


class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        return ProductSerializer

    def get_queryset(self):
        category_id = self.kwargs.get("category_pk")
        store = self.request.scope_store
        if store is None:
            return Product.objects.none()
        return Product.objects.filter(
            category__id=category_id,
            category__catalog__store=store,
        ).prefetch_related("modifier_groups__options", "channel_maps", "availability_windows")

    def perform_create(self, serializer):
        category = Category.objects.get(
            id=self.kwargs["category_pk"],
            catalog__store=self.request.scope_store,
        )
        serializer.save(category=category)

    @action(detail=False, methods=["get"], url_path="available")
    def available(self, request, **kwargs):
        """Lista produtos disponíveis agora para a store + canal opcional.

        Query param: ?channel=IFOOD
        """
        channel = request.query_params.get("channel")
        qs = get_available_products_for_store(request.scope_store, channel=channel)
        serializer = ProductListSerializer(qs, many=True)
        return Response(serializer.data)


class ProductChannelMapViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductChannelMapSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        product_id = self.kwargs.get("product_pk")
        store = self.request.scope_store
        if store is None:
            return ProductChannelMap.objects.none()
        return ProductChannelMap.objects.filter(
            product__id=product_id,
            product__category__catalog__store=store,
        )

    def perform_create(self, serializer):
        product = Product.objects.get(
            id=self.kwargs["product_pk"],
            category__catalog__store=self.request.scope_store,
        )
        serializer.save(product=product)
