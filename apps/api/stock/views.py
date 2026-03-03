import structlog
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import BillOfMaterials, StockAlert, StockItem, StockMovement
from .serializers import (
    BillOfMaterialsSerializer,
    StockAlertSerializer,
    StockItemSerializer,
    StockMovementSerializer,
)

log = structlog.get_logger()


class StockItemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = StockItemSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return StockItem.objects.filter(store=self.request.scope_store).select_related("level")

    def perform_create(self, serializer):
        serializer.save(store=self.request.scope_store)

    @action(detail=True, methods=["get"], url_path="movements")
    def movements(self, request, pk=None):
        item = self.get_object()
        qs = StockMovement.objects.filter(stock_item=item).order_by("-occurred_at")
        serializer = StockMovementSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="recalculate")
    def recalculate(self, request, pk=None):
        """Força recálculo do saldo (admin/debug)."""
        from .tasks import recalculate_stock_level

        item = self.get_object()
        recalculate_stock_level.delay(str(item.id))
        return Response({"queued": True})


class StockMovementViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = StockMovementSerializer
    http_method_names = ["get", "post", "head", "options"]  # sem PUT/PATCH/DELETE (append-only)

    def get_queryset(self):
        return StockMovement.objects.filter(store=self.request.scope_store).select_related("stock_item")

    def perform_create(self, serializer):
        serializer.save(store=self.request.scope_store, created_by=self.request.user)


class StockAlertViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = StockAlertSerializer

    def get_queryset(self):
        qs = StockAlert.objects.filter(store=self.request.scope_store).select_related("stock_item")
        only_open = self.request.query_params.get("open", "true").lower() == "true"
        if only_open:
            qs = qs.filter(is_resolved=False)
        return qs

    @action(detail=True, methods=["post"], url_path="resolve")
    def resolve(self, request, pk=None):
        alert = self.get_object()
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.save(update_fields=["is_resolved", "resolved_at"])
        return Response(StockAlertSerializer(alert).data)


class BillOfMaterialsViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = BillOfMaterialsSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return BillOfMaterials.objects.filter(stock_item__store=self.request.scope_store).select_related(
            "product", "stock_item"
        )
