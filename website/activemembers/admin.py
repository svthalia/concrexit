"""Registers admin interfaces for the activemembers module."""
import csv
import datetime

from django import forms
from django.contrib import admin, messages
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from activemembers import models
from activemembers.forms import MemberGroupForm, MemberGroupMembershipForm
from utils.snippets import datetime_to_lectureyear


class MemberGroupMembershipInlineFormSet(forms.BaseInlineFormSet):
    """Solely here for performance reasons.

    Needed because the `__str__()` of `MemberGroupMembership` (which is
    displayed above each inline form) uses the username, name of the member
    and name of the group.
    """

    def __init__(self, *args, **kwargs):
        """Initialize and set queryset."""
        super().__init__(*args, **kwargs)
        self.queryset = self.queryset.select_related("member", "group").filter(
            until=None
        )


class MemberGroupMembershipInline(admin.StackedInline):
    """Inline for group memberships."""

    model = models.MemberGroupMembership
    formset = MemberGroupMembershipInlineFormSet
    can_delete = False
    ordering = ("since",)
    extra = 0
    autocomplete_fields = ("member",)


class MemberGroupAdmin(admin.ModelAdmin):
    """Manage the member groups."""

    inlines = (MemberGroupMembershipInline,)
    form = MemberGroupForm
    list_display = ("name", "since", "until", "active", "email")
    list_filter = (
        "until",
        "active",
    )
    search_fields = ("name", "description")
    filter_horizontal = ("permissions",)

    fields = (
        "name",
        "description",
        "photo",
        "permissions",
        "since",
        "until",
        "contact_mailinglist",
        "contact_email",
        "active",
        "display_members",
    )

    @staticmethod
    def email(instance):
        if instance.contact_email:
            return instance.contact_email
        if instance.contact_mailinglist:
            return instance.contact_mailinglist.name + "@thalia.nu"
        return None


@admin.register(models.Committee)
class CommitteeAdmin(MemberGroupAdmin):
    """Manage the committees."""


@admin.register(models.Society)
class SocietyAdmin(MemberGroupAdmin):
    """Manage the societies."""


@admin.register(models.Board)
class BoardAdmin(admin.ModelAdmin):
    """Manage the board."""

    inlines = (MemberGroupMembershipInline,)
    form = MemberGroupForm
    exclude = ("is_board",)
    filter_horizontal = ("permissions",)

    fields = (
        "name",
        "description",
        "photo",
        "permissions",
        "contact_mailinglist",
        "contact_email",
        "since",
        "until",
        "display_members",
    )


class TypeFilter(admin.SimpleListFilter):
    """Filter memberships on board-only."""

    title = _("group memberships")
    parameter_name = "group_type"

    def lookups(self, request, model_admin):
        return [
            ("boards", _("Only boards")),
            ("committees", _("Only committees")),
            ("societies", _("Only societies")),
        ]

    def queryset(self, request, queryset):
        if self.value() == "boards":
            return queryset.exclude(group__board=None)
        if self.value() == "committees":
            return queryset.exclude(group__committee=None)
        if self.value() == "societies":
            return queryset.exclude(group__society=None)
        return queryset


class LectureYearFilter(admin.SimpleListFilter):
    """Filter the memberships on those started or ended in a lecture year."""

    title = _("lecture year")
    parameter_name = "lecture_year"

    def lookups(self, request, model_admin):
        current_year = datetime_to_lectureyear(timezone.now())
        first_year = datetime_to_lectureyear(
            models.MemberGroupMembership.objects.earliest("since").since
        )

        return [
            (year, f"{year}-{year + 1}") for year in range(first_year, current_year + 1)
        ]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        year = int(self.value())
        first_of_september = datetime.date(year=year, month=9, day=1)

        return queryset.exclude(until__lt=first_of_september)


class ActiveMembershipsFilter(admin.SimpleListFilter):
    """Filter the memberships by whether they are active or not."""

    title = _("active memberships")
    parameter_name = "active"

    def lookups(self, request, model_admin):
        return (
            ("active", _("Active")),
            ("inactive", _("Inactive")),
        )

    def queryset(self, request, queryset):
        now = timezone.now()

        if self.value() == "active":
            return queryset.filter(Q(until__isnull=True) | Q(until__gte=now))
        if self.value() == "inactive":
            return queryset.filter(until__lt=now)
        return queryset


@admin.register(models.MemberGroupMembership)
class MemberGroupMembershipAdmin(admin.ModelAdmin):
    """Manage the group memberships."""

    form = MemberGroupMembershipForm
    list_display = ("member", "group", "since", "until", "chair", "role")
    list_filter = ("group", TypeFilter, LectureYearFilter, ActiveMembershipsFilter)
    list_select_related = (
        "member",
        "group",
    )
    search_fields = ("member__first_name", "member__last_name", "member__email")
    date_hierarchy = "since"
    actions = ("export",)

    def changelist_view(self, request, extra_context=None):
        self.message_user(
            request,
            _(
                "Do not edit existing memberships if the "
                "chair of a group has changed, add a "
                "new membership instead."
            ),
            messages.WARNING,
        )
        return super().changelist_view(request, extra_context)

    def export(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="group_memberships.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                _("First name"),
                _("Last name"),
                _("Email"),
                _("Group"),
                _("Member since"),
                _("Member until"),
                _("Chair of the group"),
                _("Role"),
            ]
        )

        for membership in queryset:
            writer.writerow(
                [
                    membership.member.first_name,
                    membership.member.last_name,
                    membership.member.email,
                    membership.group,
                    membership.since,
                    membership.until,
                    membership.chair,
                    membership.role,
                ]
            )

        return response

    export.short_description = _("Export selected memberships")


@admin.register(models.Mentorship)
class MentorshipAdmin(admin.ModelAdmin):
    """Manage the mentorships."""

    autocomplete_fields = ("member",)
    search_fields = ("member__first_name", "member__last_name")
    list_filter = ("year",)
