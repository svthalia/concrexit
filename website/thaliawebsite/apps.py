from django.apps import AppConfig
from django.urls import reverse


class ThaliaWebsiteConfig(AppConfig):
    name = "thaliawebsite"

    def menu_items(self):
        return {"items": [{"title": "Home", "url": reverse("index"), "key": 0}]}
