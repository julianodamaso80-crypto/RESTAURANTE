import structlog
from celery.app.control import Control
from django.http import JsonResponse

from config.celery import app as celery_app

log = structlog.get_logger()


def health_worker(request):
    """Return status of active Celery workers.

    200 if at least 1 worker active, 503 otherwise.
    Timeout of 2s to avoid blocking.
    """
    try:
        control = Control(celery_app)
        ping_response = control.ping(timeout=2.0)
        workers_up = len(ping_response) > 0
        log.info("health_worker_checked", workers_active=len(ping_response))
        status_code = 200 if workers_up else 503
        return JsonResponse(
            {
                "status": "ok" if workers_up else "degraded",
                "workers": len(ping_response),
                "detail": ping_response,
            },
            status=status_code,
        )
    except Exception as exc:
        log.error("health_worker_error", error=str(exc))
        return JsonResponse({"status": "error", "detail": str(exc)}, status=503)
