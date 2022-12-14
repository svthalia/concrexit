from django.apps import AppConfig


class ThaliaWebsiteConfig(AppConfig):
    name = "thaliawebsite"

    def menu_items(self):
        return {"items": [{"title": "Home", "viewname": "index", "key": 0}]}
