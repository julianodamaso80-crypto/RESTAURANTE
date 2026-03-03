from datetime import timedelta

import structlog
from django.db.models import Avg, Count
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import KDSStation, KDSTicket, KDSTicketStatus
from .serializers import KDSStationSerializer, KDSTicketSerializer, KDSTicketStatusUpdateSerializer

log = structlog.get_logger()


class KDSStationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = KDSStationSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return KDSStation.objects.filter(store=self.request.scope_store)

    def perform_create(self, serializer):
        serializer.save(store=self.request.scope_store)

    @action(detail=True, methods=["get"], url_path="tickets")
    def tickets(self, request, pk=None):
        """Active tickets for the station (excludes DONE by default).

        Polling-friendly: ordered by enqueued_at, no pagination (KDS shows all).
        Supports ?include_done=true for history.
        """
        station = self.get_object()
        include_done = request.query_params.get("include_done", "false").lower() == "true"

        qs = KDSTicket.objects.filter(station=station).select_related("order").prefetch_related("order__items")

        if not include_done:
            qs = qs.exclude(status=KDSTicketStatus.DONE)

        serializer = KDSTicketSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="metrics")
    def metrics(self, request, pk=None):
        """Average prep time for the station (last 24h)."""
        station = self.get_object()

        since = timezone.now() - timedelta(hours=24)

        stats = KDSTicket.objects.filter(
            station=station,
            status=KDSTicketStatus.DONE,
            completed_at__gte=since,
        ).aggregate(
            avg_wait=Avg("wait_time_seconds"),
            avg_prep=Avg("prep_time_seconds"),
            total_done=Count("id"),
        )

        return Response(
            {
                "station_id": str(station.id),
                "station_name": station.name,
                "period_hours": 24,
                "total_completed": stats["total_done"] or 0,
                "avg_wait_seconds": round(stats["avg_wait"] or 0),
                "avg_prep_seconds": round(stats["avg_prep"] or 0),
            }
        )


class KDSTicketViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = KDSTicketSerializer

    def get_queryset(self):
        return (
            KDSTicket.objects.filter(station__store=self.request.scope_store)
            .select_related("order", "station")
            .prefetch_related("order__items")
        )

    def retrieve(self, request, pk=None):
        ticket = self.get_object()
        return Response(KDSTicketSerializer(ticket).data)

    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, pk=None):
        ticket = self.get_object()
        serializer = KDSTicketStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]

        try:
            if new_status == KDSTicketStatus.IN_PROGRESS:
                ticket.start()
            elif new_status == KDSTicketStatus.DONE:
                ticket.complete()
            ticket.save()
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        log.info(
            "kds_ticket_status_updated",
            ticket_id=str(ticket.id),
            new_status=new_status,
            order_id=str(ticket.order_id),
        )

        return Response(KDSTicketSerializer(ticket).data)
