from django.apps import AppConfig
from django.db.models import Count, Exists, OuterRef, Q
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from registrations.models import Renewal

from .models.member import Member


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

    def user_menu_items(self):
        return {
            "sections": [{"name": "profile", "key": 1}],
            "items": [
                {
                    "section": "profile",
                    "title": "Show public profile",
                    "url": reverse("members:profile"),
                    "key": 1,
                },
                {
                    "section": "profile",
                    "title": "Edit profile",
                    "url": reverse("members:edit-profile"),
                    "key": 2,
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
        if request.member and not request.member.has_active_membership():
            announcements.append(
                {
                    "content": render_to_string(
                        "members/announcement_not_member.html",
                        context={"member": request.member},
                    ),
                    "icon": "id-card",
                }
            )
        if request.member and request.member.profile.event_permissions != "all":
            announcements.append(
                {
                    "content": render_to_string("members/announcement_no_events.html"),
                    "icon": "exclamation",
                }
            )
        if (
            request.member
            and request.member.profile
            and not request.member.profile.photo
        ):
            announcements.append(
                {
                    "content": render_to_string("members/announcement_no_pfp.html"),
                    "icon": "address-card",
                }
            )
        return announcements

    def execute_data_minimisation(self, dry_run=False, members=None) -> list[Member]:
        """Clean the profiles of members/users of whom the last membership ended at least 90 days ago.

        :param dry_run: does not really remove data if True
        :param members: queryset of members to process, optional
        :return: list of processed members
        """
        if not members:
            members = Member.objects
        members = (
            members.annotate(membership_count=Count("membership"))
            .exclude(
                (
                    Q(membership__until__isnull=True)
                    | Q(membership__until__gt=timezone.now().date())
                )
                & Q(membership_count__gt=0)
            )
            .exclude(
                Exists(
                    Renewal.objects.filter(member__id=OuterRef("pk")).exclude(
                        status__in=(
                            Renewal.STATUS_ACCEPTED,
                            Renewal.STATUS_REJECTED,
                        )
                    )
                )
            )
            .distinct()
            .prefetch_related("membership_set", "profile")
        )
        deletion_period = timezone.now().date() - timezone.timedelta(days=90)
        processed_members = []
        for member in members:
            if (
                member.latest_membership is None
                or member.latest_membership.until <= deletion_period
            ):
                processed_members.append(member)
                profile = member.profile
                profile.student_number = None
                profile.phone_number = None
                profile.address_street = None
                profile.address_street2 = None
                profile.address_postal_code = None
                profile.address_city = None
                profile.address_country = None
                profile.birthday = None
                profile.emergency_contact_phone_number = None
                profile.emergency_contact = None
                profile.is_minimized = True
                if not dry_run:
                    profile.save()

        return processed_members
