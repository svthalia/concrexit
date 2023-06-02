from django.apps import AppConfig
from django.urls import reverse

from utils.snippets import minimise_logentries_data


class ThaliaWebsiteConfig(AppConfig):
    name = "thaliawebsite"

    def menu_items(self):
        return {"items": [{"title": "Home", "url": reverse("index"), "key": 0}]}

    def data_minimization_methods(self):
        return {"logentries": minimise_logentries_data}
