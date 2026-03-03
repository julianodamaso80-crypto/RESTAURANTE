import structlog
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    FranchiseeOnboarding,
    FranchiseTemplate,
    NetworkAlert,
    NetworkReport,
    OnboardingStatus,
    StoreOverride,
)
from .serializers import (
    FranchiseeOnboardingSerializer,
    FranchiseTemplateSerializer,
    NetworkAlertSerializer,
    NetworkReportSerializer,
    StoreOverrideSerializer,
)

log = structlog.get_logger()


class FranchiseTemplateViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FranchiseTemplateSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        return FranchiseTemplate.objects.filter(company=self.request.scope_store.company)

    def perform_create(self, serializer):
        serializer.save(company=self.request.scope_store.company)

    @action(detail=True, methods=["post"], url_path="onboard-store")
    def onboard_store(self, request, pk=None):
        """
        Provisiona uma nova store a partir deste template.
        Body: {"store_id": "<uuid>"}
        """
        from tenants.models import Store

        from .tasks import run_franchisee_onboarding

        template = self.get_object()
        store_id = request.data.get("store_id")

        if not store_id:
            return Response({"detail": "store_id é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            store = Store.objects.get(id=store_id, company=self.request.scope_store.company)
        except Store.DoesNotExist:
            return Response({"detail": "Store não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        onboarding, created = FranchiseeOnboarding.objects.get_or_create(
            template=template,
            store=store,
            defaults={"status": OnboardingStatus.PENDING},
        )

        if not created and onboarding.status == OnboardingStatus.DONE:
            return Response(
                {
                    "detail": "Onboarding já concluído para esta store.",
                    "onboarding": FranchiseeOnboardingSerializer(onboarding).data,
                },
                status=status.HTTP_200_OK,
            )

        run_franchisee_onboarding.delay(str(onboarding.id))

        log.info("onboarding_enqueued", store=store.name, template=template.name)

        return Response(
            FranchiseeOnboardingSerializer(onboarding).data,
            status=status.HTTP_202_ACCEPTED,
        )


class StoreOverrideViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = StoreOverrideSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        return StoreOverride.objects.filter(store=self.request.scope_store)


class FranchiseeOnboardingViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FranchiseeOnboardingSerializer

    def get_queryset(self):
        return FranchiseeOnboarding.objects.filter(template__company=self.request.scope_store.company)

    @action(detail=True, methods=["post"], url_path="retry")
    def retry(self, request, pk=None):
        """Retentar onboarding que falhou."""
        from .tasks import run_franchisee_onboarding

        ob = self.get_object()
        if ob.status != OnboardingStatus.FAILED:
            return Response(
                {"detail": "Só é possível retentar onboardings com status FAILED."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ob.status = OnboardingStatus.PENDING
        ob.error_detail = ""
        ob.save(update_fields=["status", "error_detail"])
        run_franchisee_onboarding.delay(str(ob.id))
        return Response(FranchiseeOnboardingSerializer(ob).data)


class NetworkReportViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NetworkReportSerializer

    def get_queryset(self):
        return NetworkReport.objects.filter(company=self.request.scope_store.company)

    @action(detail=False, methods=["post"], url_path="generate")
    def generate(self, request):
        """
        Dispara geração de relatório da rede.
        Body: {"period": "DAILY"|"WEEKLY"|"MONTHLY", "date_from": "2024-01-01", "date_to": "2024-01-31"}
        """
        from .tasks import generate_network_report_task

        period = request.data.get("period", "DAILY")
        date_from = request.data.get("date_from")
        date_to = request.data.get("date_to")

        if not date_from or not date_to:
            return Response(
                {"detail": "date_from e date_to são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        company = self.request.scope_store.company
        generate_network_report_task.delay(str(company.id), period, date_from, date_to)

        return Response(
            {"queued": True, "period": period, "date_from": date_from, "date_to": date_to},
            status=status.HTTP_202_ACCEPTED,
        )


class NetworkAlertViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NetworkAlertSerializer

    def get_queryset(self):
        qs = NetworkAlert.objects.filter(company=self.request.scope_store.company).select_related("store")
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
        return Response(NetworkAlertSerializer(alert).data)

    @action(detail=False, methods=["post"], url_path="check")
    def check(self, request):
        """Dispara verificação de alertas da rede manualmente."""
        from .tasks import check_network_alerts_task

        company = self.request.scope_store.company
        check_network_alerts_task.delay(str(company.id))
        return Response({"queued": True})
