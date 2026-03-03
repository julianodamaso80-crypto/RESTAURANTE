from django.apps import AppConfig


class CdpConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cdp"

    def ready(self):
        import cdp.signals  # noqa: F401
