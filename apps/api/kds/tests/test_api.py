import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from kds.models import KDSTicketStatus


@pytest.mark.django_db
def test_list_stations_requires_auth():
    client = APIClient()
    response = client.get("/api/v1/kds/stations/")
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_list_stations_filtered_by_store(auth_client, kds_station_factory, other_store):
    """Only returns stations for the request's scoped store."""
    from kds.tests.factories import KDSStationFactory

    my_station = kds_station_factory()
    other_station = KDSStationFactory(store=other_store)

    response = auth_client.get("/api/v1/kds/stations/")
    assert response.status_code == 200
    data = response.json()
    # DRF may return paginated {"results": [...]} or plain list
    items = data["results"] if isinstance(data, dict) and "results" in data else data
    ids = [s["id"] for s in items]

    assert str(my_station.id) in ids
    assert str(other_station.id) not in ids


@pytest.mark.django_db
def test_create_station(auth_client):
    response = auth_client.post(
        "/api/v1/kds/stations/",
        data={"name": "Grill", "category": "GRILL"},
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Grill"
    assert response.json()["category"] == "GRILL"


@pytest.mark.django_db
def test_ticket_advance_to_in_progress(auth_client, kds_ticket_factory):
    ticket = kds_ticket_factory(status=KDSTicketStatus.WAITING)
    response = auth_client.patch(
        f"/api/v1/kds/tickets/{ticket.id}/status/",
        data={"status": "IN_PROGRESS"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"


@pytest.mark.django_db
def test_ticket_advance_to_done(auth_client, kds_ticket_factory):
    ticket = kds_ticket_factory(status=KDSTicketStatus.IN_PROGRESS)
    ticket.started_at = timezone.now()
    ticket.save()

    response = auth_client.patch(
        f"/api/v1/kds/tickets/{ticket.id}/status/",
        data={"status": "DONE"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["status"] == "DONE"


@pytest.mark.django_db
def test_ticket_invalid_transition_returns_400(auth_client, kds_ticket_factory):
    ticket = kds_ticket_factory(status=KDSTicketStatus.DONE)
    response = auth_client.patch(
        f"/api/v1/kds/tickets/{ticket.id}/status/",
        data={"status": "IN_PROGRESS"},
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_station_tickets_endpoint_excludes_done(auth_client, kds_station_factory, kds_ticket_factory):
    station = kds_station_factory()
    waiting = kds_ticket_factory(station=station, status=KDSTicketStatus.WAITING)
    kds_ticket_factory(station=station, status=KDSTicketStatus.DONE)

    response = auth_client.get(f"/api/v1/kds/stations/{station.id}/tickets/")
    assert response.status_code == 200
    ids = [t["id"] for t in response.json()]

    assert str(waiting.id) in ids
    # DONE ticket should NOT be in the response
    assert len(ids) == 1


@pytest.mark.django_db
def test_station_tickets_include_done_param(auth_client, kds_station_factory, kds_ticket_factory):
    station = kds_station_factory()
    done = kds_ticket_factory(station=station, status=KDSTicketStatus.DONE)

    response = auth_client.get(f"/api/v1/kds/stations/{station.id}/tickets/?include_done=true")
    assert response.status_code == 200
    ids = [t["id"] for t in response.json()]
    assert str(done.id) in ids


@pytest.mark.django_db
def test_ticket_retrieve(auth_client, kds_ticket_factory):
    ticket = kds_ticket_factory()
    response = auth_client.get(f"/api/v1/kds/tickets/{ticket.id}/")
    assert response.status_code == 200
    assert response.json()["id"] == str(ticket.id)
