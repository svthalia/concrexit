from django.apps import AppConfig
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class PartnersConfig(AppConfig):
    """Appconfig for partners app."""

    name = "partners"
    verbose_name = _("Partners")

    def menu_items(self):
        return {
            "categories": [{"name": "career", "title": "Career", "key": 4}],
            "items": [
                {
                    "category": "career",
                    "title": "Partners",
                    "url": reverse("partners:index"),
                    "key": 0,
                },
                {
                    "category": "career",
                    "title": "Vacancies",
                    "url": reverse("partners:vacancies"),
                    "key": 1,
                },
            ],
        }
