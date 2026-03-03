from django.apps import AppConfig


class KdsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "kds"
    verbose_name = "Kitchen Display System"

    def ready(self):
        import kds.signals  # noqa: F401
