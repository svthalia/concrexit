"""Configuration for the payments package."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from payments.services import execute_data_minimisation


class PaymentsConfig(AppConfig):
    """AppConfig for the payments package."""

    name = "payments"
    verbose_name = _("Payments")

    def data_minimization_methods(self):
        return {"payments": execute_data_minimisation}
