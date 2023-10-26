from django.apps import AppConfig


class SalesConfig(AppConfig):
    name = "sales"

    def ready(self):
        from . import signals  # noqa: F401
        from .payables import register

        register()
