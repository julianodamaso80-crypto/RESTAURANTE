from datetime import datetime, time
from unittest.mock import patch

import pytest

from catalog.availability import is_product_available
from catalog.models import CatalogStatus, ProductAvailability, WeekDay


@pytest.mark.django_db
def test_active_product_with_no_windows_is_available(product_factory):
    p = product_factory(status=CatalogStatus.ACTIVE)
    assert is_product_available(p) is True


@pytest.mark.django_db
def test_inactive_product_is_not_available(product_factory):
    p = product_factory(status=CatalogStatus.INACTIVE)
    assert is_product_available(p) is False


@pytest.mark.django_db
def test_draft_product_is_not_available(product_factory):
    p = product_factory(status=CatalogStatus.DRAFT)
    assert is_product_available(p) is False


@pytest.mark.django_db
def test_product_available_in_window(product_factory):
    p = product_factory(status=CatalogStatus.ACTIVE)
    for day in range(7):
        ProductAvailability.objects.create(
            product=p,
            week_day=day,
            start_time=time(0, 0),
            end_time=time(23, 59),
        )
    assert is_product_available(p) is True


@pytest.mark.django_db
def test_product_not_available_outside_window(product_factory):
    """Produto com janela apenas na segunda, testado na terça → indisponível."""
    p = product_factory(status=CatalogStatus.ACTIVE)
    ProductAvailability.objects.create(
        product=p,
        week_day=WeekDay.MONDAY,
        start_time=time(11, 0),
        end_time=time(14, 0),
    )
    # 2024-01-09 = terça-feira
    tuesday_noon = datetime(2024, 1, 9, 12, 0)
    with patch("catalog.availability.tz.localtime", return_value=tuesday_noon):
        assert is_product_available(p) is False


@pytest.mark.django_db
def test_product_available_in_correct_window(product_factory):
    """Produto com janela na segunda, testado na segunda → disponível."""
    p = product_factory(status=CatalogStatus.ACTIVE)
    ProductAvailability.objects.create(
        product=p,
        week_day=WeekDay.MONDAY,
        start_time=time(11, 0),
        end_time=time(14, 0),
    )
    # 2024-01-08 = segunda-feira
    monday_noon = datetime(2024, 1, 8, 12, 0)
    with patch("catalog.availability.tz.localtime", return_value=monday_noon):
        assert is_product_available(p) is True


@pytest.mark.django_db
def test_product_not_available_before_window(product_factory):
    """Produto com janela 11-14, testado às 10 → indisponível."""
    p = product_factory(status=CatalogStatus.ACTIVE)
    ProductAvailability.objects.create(
        product=p,
        week_day=WeekDay.MONDAY,
        start_time=time(11, 0),
        end_time=time(14, 0),
    )
    monday_10am = datetime(2024, 1, 8, 10, 0)
    with patch("catalog.availability.tz.localtime", return_value=monday_10am):
        assert is_product_available(p) is False


@pytest.mark.django_db
def test_product_available_with_check_time(product_factory):
    """Passando check_time explicitamente."""
    p = product_factory(status=CatalogStatus.ACTIVE)
    ProductAvailability.objects.create(
        product=p,
        week_day=WeekDay.FRIDAY,
        start_time=time(18, 0),
        end_time=time(23, 0),
    )
    friday_evening = datetime(2024, 1, 12, 20, 0)  # sexta
    assert is_product_available(p, check_time=friday_evening) is True

    friday_morning = datetime(2024, 1, 12, 8, 0)
    assert is_product_available(p, check_time=friday_morning) is False
