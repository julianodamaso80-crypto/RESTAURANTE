import pytest
from django.db import IntegrityError
from django.utils import timezone

from kds.models import KDSTicketStatus


@pytest.mark.django_db
def test_ticket_start_sets_timestamps(kds_ticket_factory):
    ticket = kds_ticket_factory(status=KDSTicketStatus.WAITING)
    assert ticket.started_at is None
    ticket.start()
    assert ticket.status == KDSTicketStatus.IN_PROGRESS
    assert ticket.started_at is not None
    assert ticket.wait_time_seconds is not None
    assert ticket.wait_time_seconds >= 0


@pytest.mark.django_db
def test_ticket_complete_sets_timestamps(kds_ticket_factory):
    ticket = kds_ticket_factory(status=KDSTicketStatus.IN_PROGRESS)
    ticket.started_at = timezone.now()
    ticket.complete()
    assert ticket.status == KDSTicketStatus.DONE
    assert ticket.completed_at is not None
    assert ticket.prep_time_seconds is not None


@pytest.mark.django_db
def test_ticket_complete_from_waiting_skips_in_progress(kds_ticket_factory):
    """Operator can mark DONE directly from WAITING (skip IN_PROGRESS)."""
    ticket = kds_ticket_factory(status=KDSTicketStatus.WAITING)
    ticket.complete()
    assert ticket.status == KDSTicketStatus.DONE
    assert ticket.wait_time_seconds is not None


@pytest.mark.django_db
def test_ticket_start_from_done_raises(kds_ticket_factory):
    ticket = kds_ticket_factory(status=KDSTicketStatus.DONE)
    with pytest.raises(ValueError):
        ticket.start()


@pytest.mark.django_db
def test_ticket_complete_from_done_raises(kds_ticket_factory):
    ticket = kds_ticket_factory(status=KDSTicketStatus.DONE)
    with pytest.raises(ValueError):
        ticket.complete()


@pytest.mark.django_db
def test_station_unique_name_per_store(kds_station_factory):
    station = kds_station_factory()
    with pytest.raises(IntegrityError):
        kds_station_factory(store=station.store, name=station.name)
