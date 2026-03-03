import structlog
import structlog.contextvars


def test_structlog_binds_request_id():
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id="abc-123", correlation_id="xyz-789")
    ctx = structlog.contextvars.get_contextvars()
    assert ctx["request_id"] == "abc-123"
    assert ctx["correlation_id"] == "xyz-789"
    structlog.contextvars.clear_contextvars()


def test_structlog_clears_between_requests():
    structlog.contextvars.bind_contextvars(request_id="req-1")
    structlog.contextvars.clear_contextvars()
    ctx = structlog.contextvars.get_contextvars()
    assert "request_id" not in ctx


def test_structlog_logger_works():
    """Smoke test — logger does not raise."""
    log = structlog.get_logger()
    log.info("test_event", key="value")
