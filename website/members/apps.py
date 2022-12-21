"""Configuration for the members package."""
from django.apps import AppConfig
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class MembersConfig(AppConfig):
    name = "members"
    verbose_name = _("Members")

    def menu_items(self):
        return {
            "categories": [{"name": "members", "title": "For Members", "key": 2}],
            "items": [
                {
                    "category": "members",
                    "title": "Member list",
                    "url": reverse("members:index"),
                    "key": 0,
                },
                {
                    "category": "members",
                    "title": "Statistics",
                    "url": reverse("members:statistics"),
                    "key": 2,
                },
                {
                    "category": "members",
                    "title": "G Suite Knowledge Base",
                    "url": "https://gsuite.members.thalia.nu/",
                    "authenticated": True,
                    "key": 6,
                },
            ],
        }
