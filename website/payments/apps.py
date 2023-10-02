"""Configuration for the payments package."""
from django.apps import AppConfig
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class PaymentsConfig(AppConfig):
    """AppConfig for the payments package."""

    name = "payments"
    verbose_name = _("Payments")

    def user_menu_items(self):
        return {
            "sections": [{"name": "membership", "key": 2}],
            "items": [
                {
                    "section": "membership",
                    "title": "Manage bank account(s)",
                    "url": reverse("payments:bankaccount-list"),
                    "key": 2,
                },
                {
                    "section": "membership",
                    "title": "View payments",
                    "url": reverse("payments:payment-list"),
                    "key": 3,
                },
            ],
        }
