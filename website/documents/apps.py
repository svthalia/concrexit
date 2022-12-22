from django.apps import AppConfig
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class DocumentsConfig(AppConfig):
    name = "documents"
    verbose_name = _("Documents")

    def menu_items(self):
        return {
            "categories": [{"name": "association", "title": "Association", "key": 1}],
            "items": [
                {
                    "category": "association",
                    "title": "Documents",
                    "url": reverse("documents:index"),
                    "key": 3,
                },
            ],
        }
