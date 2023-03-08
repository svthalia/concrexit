"""Configuration for the members package."""
from django.apps import AppConfig
from django.template.loader import render_to_string
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

    def announcements(self, request) -> list[dict]:
        # Skip announcements for anonymous users to prevent evaluating
        # request.member too early for API requests, because DRF only sets
        # the correct request.user after evaluating the middlewares.
        if request.user.is_anonymous:
            return []

        announcements = []
        if request.member and request.member.current_membership is None:
            announcements.append(
                {"rich_text": render_to_string("members/announcement_not_member.html")}
            )
        if request.member and request.member.profile.event_permissions != "all":
            announcements.append(
                {"rich_text": render_to_string("members/announcement_no_events.html")}
            )
        if (
            request.member
            and request.member.profile
            and not request.member.profile.photo
        ):
            announcements.append(
                {"rich_text": render_to_string("members/announcement_no_pfp.html")}
            )
        return announcements
