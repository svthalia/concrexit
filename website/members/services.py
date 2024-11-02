"""Services defined in the members package."""
from collections.abc import Callable
from datetime import date
from typing import Any

from django.conf import settings
from django.db.models import Count, Exists, OuterRef, Q
from django.utils import timezone

from members import emails
from members.models import Member, Membership
from registrations.models import Renewal
from utils.snippets import datetime_to_lectureyear


def _member_group_memberships(
    member: Member, condition: Callable[[Membership], bool]
) -> dict[str, dict[str, Any]]:
    """Determine the group membership of a user based on a condition.

    :return: Object with group memberships
    """
    memberships = member.membergroupmembership_set.all()
    data = {}

    for membership in memberships:
        if not condition(membership):
            continue
        period = {
            "since": membership.since,
            "until": membership.until,
            "chair": membership.chair,
        }

        if hasattr(membership.group, "board"):
            period["role"] = membership.role

        if membership.until is None and hasattr(membership.group, "board"):
            period["until"] = membership.group.board.until

        name = membership.group.name
        if data.get(name):
            data[name]["periods"].append(period)
            if data[name]["earliest"] > period["since"]:
                data[name]["earliest"] = period["since"]
            if period["until"] is None or (
                data[name]["latest"] is not None
                and data[name]["latest"] < period["until"]
            ):
                data[name]["latest"] = period["until"]
            data[name]["periods"].sort(key=lambda x: x["since"])
        else:
            data[name] = {
                "pk": membership.group.pk,
                "active": membership.group.active,
                "name": name,
                "periods": [period],
                "url": settings.BASE_URL + membership.group.get_absolute_url(),
                "earliest": period["since"],
                "latest": period["until"],
            }
    return data


def member_achievements(member) -> list:
    """Derive a list of achievements of a member.

    Committee and board memberships + mentorships
    """
    achievements = _member_group_memberships(
        member,
        lambda membership: (
            hasattr(membership.group, "board") or hasattr(membership.group, "committee")
        ),
    )

    mentor_years = member.mentorship_set.all()
    for mentor_year in mentor_years:
        name = f"Mentor in {mentor_year.year}"
        # Ensure mentorships appear last but are sorted
        earliest = date.today()
        # Making sure it does not crash in leap years
        if earliest.month == 2 and earliest.day == 29:
            earliest = earliest.replace(day=28)

        earliest = earliest.replace(year=earliest.year + mentor_year.year)

        if not achievements.get(name):
            achievements[name] = {
                "name": name,
                "earliest": earliest,
            }
    return sorted(achievements.values(), key=lambda x: x["earliest"])


def member_societies(member) -> list:
    """Derive a list of societies a member was part of."""
    societies = _member_group_memberships(
        member, lambda membership: (hasattr(membership.group, "society"))
    )
    return sorted(societies.values(), key=lambda x: x["earliest"])


def gen_stats_member_type() -> dict[str, list]:
    """Generate statistics about membership types."""
    data = {
        "labels": [],
        "datasets": [
            {"data": []},
        ],
    }

    for key, display in Membership.MEMBERSHIP_TYPES:
        data["labels"].append(str(display))
        data["datasets"][0]["data"].append(
            Membership.objects.filter(since__lte=date.today())
            .filter(Q(until__isnull=True) | Q(until__gt=date.today()))
            .filter(type=key)
            .count()
        )

    return data


def gen_stats_year() -> dict[str, list]:
    """Generate statistics on how many members (and other membership types) there were in each year."""
    years = range(2015, datetime_to_lectureyear(date.today()) + 1)

    data = {
        "labels": list(years),
        "datasets": [
            {"label": str(display), "data": []}
            for _, display in Membership.MEMBERSHIP_TYPES
        ],
    }

    for index, (key, _) in enumerate(Membership.MEMBERSHIP_TYPES):
        for year in years:
            data["datasets"][index]["data"].append(
                Membership.objects.filter(since__lte=date(year=year, month=10, day=1))
                .filter(
                    Q(until__isnull=True)
                    | Q(until__gt=date(year=year, month=10, day=1))
                )
                .filter(type=key)
                .count()
            )

    return data


def gen_stats_active_members() -> dict[str, list]:
    """Generate statistics about active members."""
    return {
        "labels": ["Active Members", "Non-active Members"],
        "datasets": [
            {
                "data": [
                    Member.active_members.count(),
                    Member.current_members.count() - Member.active_members.count(),
                ]
            }
        ],
    }


def verify_email_change(change_request) -> None:
    """Mark the email change request as verified.

    :param change_request: the email change request
    """
    change_request.verified = True
    change_request.save()

    process_email_change(change_request)


def confirm_email_change(change_request) -> None:
    """Mark the email change request as verified.

    :param change_request: the email change request
    """
    change_request.confirmed = True
    change_request.save()

    process_email_change(change_request)


def process_email_change(change_request) -> None:
    """Change the user's email address if the request was completed and send the completion email.

    :param change_request: the email change request
    """
    if not change_request.completed:
        return

    member = change_request.member
    member.email = change_request.email
    member.save()

    emails.send_email_change_completion_message(change_request)


def execute_data_minimisation(dry_run=False, members=None) -> list[Member]:
    """Clean the profiles of members/users of whom the last membership ended at least 31 days ago.

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
