from django.apps import AppConfig
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
                    "viewname": "partners:index",
                    "key": 0,
                },
                {
                    "category": "career",
                    "title": "Vacancies",
                    "viewname": "partners:vacancies",
                    "key": 1,
                },
            ],
        }
