import structlog
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .consent import grant_consent, revoke_consent
from .models import ConsentRecord, Customer, CustomerEvent
from .serializers import (
    ConsentRecordSerializer,
    ConsentUpdateSerializer,
    CustomerEventSerializer,
    CustomerSerializer,
)

log = structlog.get_logger()


class CustomerViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        tenant = self.request.scope_tenant
        if tenant is None:
            return Customer.objects.none()
        return Customer.objects.filter(tenant=tenant).prefetch_related("identities")

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.scope_tenant)

    @action(detail=True, methods=["get"], url_path="events")
    def events(self, request, pk=None):
        customer = self.get_object()
        qs = CustomerEvent.objects.filter(customer=customer).order_by("-occurred_at")
        serializer = CustomerEventSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="consents")
    def consents(self, request, pk=None):
        """Histórico completo de consentimentos (append-only)."""
        customer = self.get_object()
        qs = ConsentRecord.objects.filter(customer=customer).order_by("-created_at")
        serializer = ConsentRecordSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="consent")
    def update_consent(self, request, pk=None):
        """Registrar grant ou revoke de consentimento para um canal."""
        customer = self.get_object()
        serializer = ConsentUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        kwargs = {
            "source": data.get("source", "api"),
            "legal_basis": data.get("legal_basis", ""),
            "ip_address": request.META.get("REMOTE_ADDR"),
        }

        if data["action"] == "grant":
            record = grant_consent(customer, data["channel"], **kwargs)
        else:
            record = revoke_consent(customer, data["channel"], **kwargs)

        return Response(ConsentRecordSerializer(record).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="trigger-rfv")
    def trigger_rfv(self, request, pk=None):
        """Dispara recálculo RFV manual (para admin/debug)."""
        from .tasks import recalculate_customer_rfv

        customer = self.get_object()
        recalculate_customer_rfv.delay(str(customer.id))
        return Response({"queued": True})
