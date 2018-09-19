from datetime import date

from django.db.models import Q
from django.utils import timezone

from members import emails
from members.models import Membership, Member
from utils.snippets import datetime_to_lectureyear


def member_achievements(member):
    memberships = member.membergroupmembership_set.all()
    achievements = {}
    for membership in memberships:
        period = {
            'since': membership.since,
            'until': membership.until,
            'chair': membership.chair
        }

        if hasattr(membership.committee, 'board'):
            period['role'] = membership.role

        if (membership.until is None and
                hasattr(membership.committee, 'board')):
            period['until'] = membership.committee.board.until

        name = membership.committee.name
        if achievements.get(name):
            achievements[name]['periods'].append(period)
            if achievements[name]['earliest'] > membership.since:
                achievements[name]['earliest'] = membership.since
            achievements[name]['periods'].sort(key=lambda x: x['since'])
        else:
            achievements[name] = {
                'name': name,
                'periods': [period],
                'earliest': membership.since,
            }
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


def gen_stats_member_type(member_types):
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


def gen_stats_year(member_types):
    """
    Generate list with 6 entries, where each entry represents the total amount
    of Thalia members in a year. The sixth element contains all the multi-year
    students.
    """
    stats_year = []
    current_year = datetime_to_lectureyear(date.today())

    for i in range(5):
        new = dict()
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


def verify_email_change(change_request):
    """
    Mark the email change request as verified

    :param change_request: the email change request
    """
    change_request.verified = True
    change_request.save()

    process_email_change(change_request)


def confirm_email_change(change_request):
    """
    Mark the email change request as verified

    :param change_request: the email change request
    """
    change_request.confirmed = True
    change_request.save()

    process_email_change(change_request)


def process_email_change(change_request):
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


def execute_data_minimisation(dry_run=False):
    """
    Clean the profiles of members/users of whom the last membership ended
    at least 31 days ago

    :param dry_run: does not really remove data if True
    :return list of processed members
    """
    members = (Member.objects
               .filter(Q(membership__until__isnull=False) |
                       Q(membership__until__lte=timezone.now().date()))
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
            profile.birthday = None
            profile.emergency_contact_phone_number = None
            profile.emergency_contact = None
            profile.website = None
            profile.bank_account = None
            if not dry_run:
                profile.save()

    return processed_members
