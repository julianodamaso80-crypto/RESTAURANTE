import pytest

from core.tasks import example_async_task


def test_example_task_executes_sync():
    """Test the task synchronously (no broker)."""
    result = example_async_task({"key": "value"}, correlation_id="test-corr")
    assert result["processed"] is True
    assert "key" in result["input_keys"]


def test_example_task_call_local():
    """Ensure the task can be called locally without Celery running."""
    result = example_async_task.apply(args=[{"foo": "bar"}]).get()
    assert result["processed"] is True


@pytest.mark.django_db
def test_task_is_registered():
    """Confirm the task is registered in the Celery app."""
    from config.celery import app

    assert "core.tasks.example_async_task" in app.tasks
