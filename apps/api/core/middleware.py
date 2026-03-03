import uuid

import structlog.contextvars


class RequestIDMiddleware:
    """Generate request_id per request and propagate correlation_id.

    - request_id: unique UUID per request
    - correlation_id: from X-Correlation-ID header, or generated if missing
    Both are injected into structlog context for all logs within the request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = str(uuid.uuid4())
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

        request.request_id = request_id
        request.correlation_id = correlation_id

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            correlation_id=correlation_id,
        )

        response = self.get_response(request)

        response["X-Request-ID"] = request_id
        response["X-Correlation-ID"] = correlation_id

        structlog.contextvars.clear_contextvars()
        return response
