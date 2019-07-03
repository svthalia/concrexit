"""Services defined in the members package"""
from datetime import date
from typing import Callable, List, Dict, Union, Any

from django.db.models import Q, Count
from django.utils import timezone
from django.utils.translation import gettext

from members import emails
from members.models import Membership, Member
from utils.snippets import datetime_to_lectureyear


def _member_group_memberships(
        member: Member, skip_condition: Callable[[Membership], bool]
) -> Dict[str, Any]:
    """
    Determines the group membership of a user based on a condition
    :return: Object with group memberships
    """
    memberships = member.membergroupmembership_set.all()
    data = {}

    for membership in memberships:
        if skip_condition(membership):
            continue
        period = {
            'since': membership.since,
            'until': membership.until,
            'chair': membership.chair
        }

        if hasattr(membership.group, 'board'):
            period['role'] = membership.role

        if (membership.until is None and
                hasattr(membership.group, 'board')):
            period['until'] = membership.group.board.until

        name = membership.group.name
        if data.get(name):
            data[name]['periods'].append(period)
            if data[name]['earliest'] > membership.since:
                data[name]['earliest'] = membership.since
            data[name]['periods'].sort(key=lambda x: x['since'])
        else:
            data[name] = {
                'name': name,
                'periods': [period],
                'url': membership.group.get_absolute_url(),
                'earliest': membership.since,
            }
    return data


def member_achievements(member) -> List:
    """
    Derives a list of achievements of a member
    Committee and board memberships + mentorships
    """
    achievements = _member_group_memberships(
        member, lambda membership: hasattr(membership, 'society'))

    mentor_years = member.mentorship_set.all()
    for mentor_year in mentor_years:
        name = "Mentor in {}".format(mentor_year.year)
        # Ensure mentorships appear last but are sorted
        earliest = date.today()
        earliest = earliest.replace(year=earliest.year + mentor_year.year)
        if not achievements.get(name):
            achievements[name] = {
                'name': name,
                'earliest': earliest,
            }
    return sorted(achievements.values(), key=lambda x: x['earliest'])


def member_societies(member) -> List:
    """
    Derives a list of societies a member was part of
    """
    societies = _member_group_memberships(member, lambda membership: (
        hasattr(membership.group, 'board') or
        hasattr(membership.group, 'committee')))
    return sorted(societies.values(), key=lambda x: x['earliest'])


def gen_stats_member_type(member_types) -> Dict[str, int]:
    """
    Generate a dictionary where every key is a member type with
    the value being the number of current members of that type
    """
    total = dict()
    for member_type in member_types:
        total[member_type] = (Membership
                              .objects
                              .filter(since__lte=date.today())
                              .filter(Q(until__isnull=True) |
                                      Q(until__gt=date.today()))
                              .filter(type=member_type)
                              .count())
    return total


def gen_stats_year(
        member_types) -> List[Dict[Union[str, Any], Union[int, Any]]]:
    """
    Generate list with 6 entries, where each entry represents the total amount
    of Thalia members in a year. The sixth element contains all the multi-year
    students.
    """
    stats_year = []
    current_year = datetime_to_lectureyear(date.today())

    for i in range(5):
        new = dict()
        new['cohort'] = current_year - i
        for member_type in member_types:
            new[member_type] = (
                Membership.objects
                .filter(user__profile__starting_year=current_year - i)
                .filter(since__lte=date.today())
                .filter(Q(until__isnull=True) |
                        Q(until__gt=date.today()))
                .filter(type=member_type)
                .count())
        stats_year.append(new)

    # Add multi year members
    new = dict()
    new['cohort'] = gettext('Older')
    for member_type in member_types:
        new[member_type] = (
            Membership.objects
            .filter(user__profile__starting_year__lt=current_year - 4)
            .filter(since__lte=date.today())
            .filter(Q(until__isnull=True) |
                    Q(until__gt=date.today()))
            .filter(type=member_type)
            .count())
    stats_year.append(new)

    return stats_year


def verify_email_change(change_request) -> None:
    """
    Mark the email change request as verified

    :param change_request: the email change request
    """
    change_request.verified = True
    change_request.save()

    process_email_change(change_request)


def confirm_email_change(change_request) -> None:
    """
    Mark the email change request as verified

    :param change_request: the email change request
    """
    change_request.confirmed = True
    change_request.save()

    process_email_change(change_request)


def process_email_change(change_request) -> None:
    """
    Change the user's email address if the request was completed and
    send the completion email

    :param change_request: the email change request
    """
    if not change_request.completed:
        return

    member = change_request.member
    member.email = change_request.email
    member.save()

    emails.send_email_change_completion_message(change_request)


def execute_data_minimisation(dry_run=False, members=None) -> List[Member]:
    """
    Clean the profiles of members/users of whom the last membership ended
    at least 31 days ago

    :param dry_run: does not really remove data if True
    :param members: queryset of members to process, optional
    :return: list of processed members
    """
    if not members:
        members = Member.objects
    members = (members.annotate(membership_count=Count('membership'))
               .exclude((Q(membership__until__isnull=True) |
                         Q(membership__until__gt=timezone.now().date())) &
                        Q(membership_count__gt=0))
               .distinct()
               .prefetch_related('membership_set', 'profile'))
    deletion_period = timezone.now().date() - timezone.timedelta(days=31)
    processed_members = []
    for member in members:
        if (member.latest_membership is None or
                member.latest_membership.until <= deletion_period):
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
            profile.website = None
            member.bank_accounts.all().delete()
            if not dry_run:
                profile.save()

    return processed_members
