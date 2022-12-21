"""Configuration for the members package."""
from django.apps import AppConfig
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _


class MembersConfig(AppConfig):
    name = "members"
    verbose_name = _("Members")

    def announcements(self, request):
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
