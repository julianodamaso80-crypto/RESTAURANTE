import structlog
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .billing import get_quota_status
from .models import Campaign, CampaignRun, CampaignStatus, CampaignTemplate, CustomerSegment
from .segmentation import estimate_segment_size
from .serializers import (
    CampaignRunSerializer,
    CampaignSerializer,
    CampaignTemplateSerializer,
    CustomerSegmentSerializer,
)

log = structlog.get_logger()


class CustomerSegmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerSegmentSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return CustomerSegment.objects.filter(tenant=self.request.scope_tenant)

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.scope_tenant)

    @action(detail=True, methods=["get"], url_path="preview")
    def preview(self, request, pk=None):
        """Preview do segmento: quantos clientes e primeiros 10."""
        segment = self.get_object()
        from cdp.serializers import CustomerSerializer

        from .segmentation import evaluate_segment

        qs = evaluate_segment(segment)[:10]
        return Response(
            {
                "total": estimate_segment_size(segment),
                "sample": CustomerSerializer(qs, many=True).data,
            }
        )


class CampaignTemplateViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CampaignTemplateSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return CampaignTemplate.objects.filter(tenant=self.request.scope_tenant)

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.scope_tenant)


class CampaignViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CampaignSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        return (
            Campaign.objects.filter(tenant=self.request.scope_tenant)
            .select_related("segment", "template")
            .prefetch_related("runs")
        )

    def perform_create(self, serializer):
        store = self.request.scope_store
        serializer.save(tenant=store.company.tenant, store=store)

    @action(detail=True, methods=["post"], url_path="launch")
    def launch(self, request, pk=None):
        """Lança uma campanha manualmente.

        Cria CampaignRun e enfileira execute_campaign_run.
        """
        from .tasks import execute_campaign_run

        campaign = self.get_object()

        if campaign.status not in (CampaignStatus.DRAFT, CampaignStatus.SCHEDULED):
            return Response(
                {"detail": f"Campanha em status '{campaign.status}' não pode ser lançada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        run = CampaignRun.objects.create(campaign=campaign)
        campaign.status = CampaignStatus.RUNNING
        campaign.save(update_fields=["status"])

        execute_campaign_run.delay(str(run.id))

        log.info(
            "campaign_launched",
            campaign_id=str(campaign.id),
            run_id=str(run.id),
        )

        return Response(CampaignRunSerializer(run).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="runs")
    def runs(self, request, pk=None):
        campaign = self.get_object()
        runs = campaign.runs.all()
        return Response(CampaignRunSerializer(runs, many=True).data)


class BillingQuotaViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="quota")
    def quota(self, request):
        """Status atual da quota de contatos do tenant."""
        return Response(get_quota_status(request.scope_tenant))
