import structlog
import structlog.contextvars
from celery import shared_task

log = structlog.get_logger()


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def example_async_task(self, payload: dict, correlation_id: str = None):
    """Example task to validate Celery + structlog integration.

    Will be replaced by real tasks in PR 4 (iFood).
    """
    if correlation_id:
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

    log.info("example_task_started", payload_keys=list(payload.keys()))

    result = {"processed": True, "input_keys": list(payload.keys())}

    log.info("example_task_completed", result=result)
    return result
