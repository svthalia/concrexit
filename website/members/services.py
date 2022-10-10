"""Services defined in the members package."""
from datetime import date, datetime
from typing import Callable, List, Dict, Any

from django.conf import settings
from django.db.models import Q, Count
from django.utils import timezone

from members import emails
from members.models import Membership, Member
from utils.snippets import datetime_to_lectureyear


def _member_group_memberships(
    member: Member, condition: Callable[[Membership], bool]
) -> Dict[str, Any]:
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


def member_achievements(member) -> List:
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
        earliest = earliest.replace(year=earliest.year + mentor_year.year)
        # Making sure it does not crash in leap years
        if earliest.month == 2 and earliest.day == 29:
            earliest = earliest.replace(day=28)
        if not achievements.get(name):
            achievements[name] = {
                "name": name,
                "earliest": earliest,
            }
    return sorted(achievements.values(), key=lambda x: x["earliest"])


def member_societies(member) -> List:
    """Derive a list of societies a member was part of."""
    societies = _member_group_memberships(
        member, lambda membership: (hasattr(membership.group, "society"))
    )
    return sorted(societies.values(), key=lambda x: x["earliest"])


def gen_stats_member_type() -> Dict:
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


def gen_stats_year() -> Dict:
    """Generate statistics on how many members (and other membership types) there were in each cohort."""
    years = range(2015, datetime_to_lectureyear(date.today()))

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
                Membership.objects.filter(since__lte=date(year=year, month=9, day=1))
                .filter(
                    Q(until__isnull=True) | Q(until__gt=date(year=year, month=9, day=1))
                )
                .filter(type=key)
                .count()
            )

    return data


def gen_stats_active_members() -> Dict:
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


def execute_data_minimisation(dry_run=False, members=None) -> List[Member]:
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
        .distinct()
        .prefetch_related("membership_set", "profile")
    )
    deletion_period = timezone.now().date() - timezone.timedelta(days=31)
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
            profile.address_street = "<removed> 1"
            profile.address_street2 = None
            profile.address_postal_code = "<removed>"
            profile.address_city = "<removed>"
            profile.address_country = "NL"
            profile.birthday = datetime(1900, 1, 1)
            profile.emergency_contact_phone_number = None
            profile.emergency_contact = None
            if not dry_run:
                profile.save()

    return processed_members
