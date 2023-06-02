from django.apps import AppConfig

from pizzas.services import execute_data_minimisation


class SalesConfig(AppConfig):
    name = "sales"

    def ready(self):
        # pylint: disable=unused-import,import-outside-toplevel
        from .payables import register

        register()

    def data_minimization_methods(self):
        return {"sales": execute_data_minimisation}
