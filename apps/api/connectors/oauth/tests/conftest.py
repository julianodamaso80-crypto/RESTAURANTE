import pytest
from rest_framework.test import APIClient

from orders.tests.factories import StoreFactory, UserFactory
from tenants.models import Membership


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def store(db):
    return StoreFactory()


@pytest.fixture
def user_with_membership(user, store):
    """User with Membership linking them to the store's tenant."""
    Membership.objects.create(
        user=user,
        tenant=store.company.tenant,
    )
    return user


@pytest.fixture
def api_client():
    return APIClient()
