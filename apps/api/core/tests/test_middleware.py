import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from core.middleware import RequestIDMiddleware


@pytest.fixture
def rf():
    return RequestFactory()


def get_response(request):
    return HttpResponse("ok")


def test_request_id_generated(rf):
    middleware = RequestIDMiddleware(get_response)
    request = rf.get("/api/v1/health/")
    response = middleware(request)
    assert hasattr(request, "request_id")
    assert len(request.request_id) == 36
    assert "X-Request-ID" in response


def test_correlation_id_from_header(rf):
    middleware = RequestIDMiddleware(get_response)
    request = rf.get("/api/v1/health/", HTTP_X_CORRELATION_ID="my-corr-id")
    middleware(request)
    assert request.correlation_id == "my-corr-id"


def test_correlation_id_generated_if_missing(rf):
    middleware = RequestIDMiddleware(get_response)
    request = rf.get("/api/v1/health/")
    middleware(request)
    assert len(request.correlation_id) == 36


def test_response_headers_set(rf):
    middleware = RequestIDMiddleware(get_response)
    request = rf.get("/")
    response = middleware(request)
    assert "X-Request-ID" in response
    assert "X-Correlation-ID" in response
