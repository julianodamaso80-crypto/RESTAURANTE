import structlog.contextvars
from celery.signals import task_postrun, task_prerun


@task_prerun.connect
def setup_task_logging(task_id, task, *args, **kwargs):
    """Inject task_id into structlog context for each worker task."""
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        task_id=task_id,
        task_name=task.name,
        correlation_id=kwargs.get("kwargs", {}).get("correlation_id", "N/A"),
    )


@task_postrun.connect
def cleanup_task_logging(*args, **kwargs):
    structlog.contextvars.clear_contextvars()
