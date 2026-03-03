import pytest
from django.utils import timezone

from kds.models import KDSTicketStatus


@pytest.mark.django_db
def test_metrics_returns_averages(auth_client, kds_station_factory, kds_ticket_factory):
    station = kds_station_factory()

    for wait, prep in [(30, 120), (60, 180), (45, 150)]:
        kds_ticket_factory(
            station=station,
            status=KDSTicketStatus.DONE,
            wait_time_seconds=wait,
            prep_time_seconds=prep,
            completed_at=timezone.now(),
        )

    response = auth_client.get(f"/api/v1/kds/stations/{station.id}/metrics/")
    data = response.json()

    assert response.status_code == 200
    assert data["total_completed"] == 3
    assert data["avg_wait_seconds"] == 45  # (30+60+45)/3
    assert data["avg_prep_seconds"] == 150  # (120+180+150)/3


@pytest.mark.django_db
def test_metrics_empty_station(auth_client, kds_station_factory):
    station = kds_station_factory()
    response = auth_client.get(f"/api/v1/kds/stations/{station.id}/metrics/")
    data = response.json()
    assert data["total_completed"] == 0
    assert data["avg_wait_seconds"] == 0
    assert data["avg_prep_seconds"] == 0
