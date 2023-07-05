from django.apps import AppConfig
from django.urls import reverse


class ThaliaWebsiteConfig(AppConfig):
    name = "thaliawebsite"

    def menu_items(self):
        return {"items": [{"title": "Home", "url": reverse("index"), "key": 0}]}

    def user_menu_items(self):
        return {
            "sections": [{"name": "general", "key": 3}, {"name": "profile", "key": 1}],
            "items": [
                {
                    "section": "general",
                    "title": "Site administration",
                    "url": reverse("admin:index"),
                    "show": lambda request: request.user.is_staff,
                    "key": 0,
                },
                {
                    "section": "general",
                    "title": "Log out",
                    "url": reverse("logout"),
                    "key": 1,
                },
                {
                    "section": "profile",
                    "title": "Authorised applications",
                    "url": reverse("oauth2_provider:authorized-token-list"),
                    "key": 3,
                },
                {
                    "section": "profile",
                    "title": "Change password",
                    "url": reverse("password_change"),
                    "key": 4,
                },
            ],
        }
