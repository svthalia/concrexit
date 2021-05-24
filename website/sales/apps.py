from django.apps import AppConfig


class SalesConfig(AppConfig):
    name = "sales"

    def ready(self):
        # pylint: disable=unused-import,import-outside-toplevel
        from .payables import register

        register()
