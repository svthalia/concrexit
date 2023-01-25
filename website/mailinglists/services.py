"""The services defined by the mailinglists package."""

from django.conf import settings
from django.utils import timezone

from activemembers.models import (
    Board,
    Committee,
    MemberGroupMembership,
    Mentorship,
    Society,
)
from members.models import Member, Membership
from utils.snippets import datetime_to_lectureyear


def get_automatic_lists():
    """Return list of mailing lists that should be generated automatically."""
    current_committee_chairs = (
        MemberGroupMembership.active_objects.filter(group__board=None)
        .filter(group__society=None)
        .filter(chair=True)
        .select_related("member")
    )
    committee_chairs = _get_members_email_addresses(
        [x.member for x in current_committee_chairs]
    ) + ["internalaffairs@thalia.nu"]

    current_society_chairs = (
        MemberGroupMembership.active_objects.filter(group__board=None)
        .filter(group__committee=None)
        .filter(chair=True)
        .select_related("member")
    )
    society_chair_emails = _get_members_email_addresses(
        [x.member for x in current_society_chairs]
    ) + ["internalaffairs@thalia.nu"]

    active_committee_memberships = (
        MemberGroupMembership.active_objects.filter(group__board=None)
        .filter(group__society=None)
        .select_related("member")
    )

    active_members = _get_members_email_addresses(
        [x.member for x in active_committee_memberships]
    )

    lectureyear = datetime_to_lectureyear(timezone.now())
    # Change to next lecture year after December
    if 0 < timezone.now().month < 9:
        lectureyear += 1
    active_mentorships = Mentorship.objects.filter(year=lectureyear).prefetch_related(
        "member"
    )
    mentors = _get_members_email_addresses([x.member for x in active_mentorships])

    alumni = [
        m
        for m in Member.objects.all()
        if m.current_membership_type == Membership.HONORARY
        or (m.has_been_member() and not m.has_active_membership())
    ]

    lists = [
        {
            "name": "members",
            "aliases": ["leden"],
            "description": "Automatic moderated mailinglist that can be used "
            "to send mail to all members",
            "addresses": _get_members_email_addresses(
                Member.all_with_membership(Membership.MEMBER)
            ),
            "moderated": True,
        },
        {
            "name": "benefactors",
            "aliases": ["begunstigers"],
            "description": "Automatic moderated mailinglist that can be used "
            "to send mail to all benefactors",
            "addresses": _get_members_email_addresses(
                Member.all_with_membership(Membership.BENEFACTOR)
            ),
            "moderated": True,
        },
        {
            "name": "honorary",
            "aliases": ["ereleden"],
            "description": "Automatic moderated mailinglist that can be used "
            "to send mail to all honorary members",
            "addresses": _get_members_email_addresses(
                Member.all_with_membership(Membership.HONORARY)
            ),
            "moderated": True,
        },
        {
            "name": "alumni",
            "description": "Automatic moderated mailinglist that can be used "
            "to send mail to all former members, including honorary members. "
            "Current members and benefactors are filtered out.",
            "addresses": _get_members_email_addresses(alumni),
            "moderated": True,
        },
        {
            "name": "all",
            "aliases": ["allen"],
            "description": "Automatic moderated mailinglist that can be used "
            "to send mail to all members, benefactors, honorary members",
            "addresses": _get_members_email_addresses(
                Member.all_with_membership(Membership.MEMBER)
                + Member.all_with_membership(Membership.BENEFACTOR)
                + Member.all_with_membership(Membership.HONORARY)
            ),
            "moderated": True,
        },
        {
            "name": "mentors",
            "description": "Automatic moderated mailinglist that can be used "
            "to send mail to all orientation mentors. These "
            "members should have a mentorship with the current "
            "calendar year.",
            "addresses": mentors,
            "moderated": True,
        },
        {
            "name": "activemembers",
            "description": "Automatic moderated mailinglist that can be used "
            "to send mail to all active members. These are all "
            "users that are currently a member of a committee.",
            "addresses": active_members,
            "moderated": True,
        },
        {
            "name": "committeechairs",
            "aliases": ["commissievoorzitters"],
            "description": "Automatic mailinglist that can be used to send "
            "mail to all committee chairs",
            "addresses": committee_chairs,
            "moderated": False,
        },
        {
            "name": "societychairs",
            "aliases": ["gezelschapvoorzitters"],
            "description": "Automatic mailinglist that can be used to send "
            "mail to all society chairs",
            "addresses": society_chair_emails,
            "moderated": False,
        },
        {
            "name": "optin",
            "description": "Automatic mailinglist that can be used to send "
            "mail to all members that have opted-in to receive "
            "these (mostly recruitment) emails.",
            "addresses": _get_members_email_addresses(
                Member.current_members.filter(profile__receive_optin=True)
            ),
            "moderated": True,
        },
        {
            "name": "committees",
            "description": "Automatic moderated mailinglist that is a "
            "collection of all committee lists",
            "addresses": [
                f"{c.contact_mailinglist.name}@{settings.GSUITE_DOMAIN}"
                for c in Committee.objects.exclude(
                    contact_mailinglist=None
                ).select_related("contact_mailinglist")
            ],
            "moderated": True,
        },
        {
            "name": "societies",
            "description": "Automatic moderated mailinglist that is a "
            "collection of all society lists",
            "addresses": [
                f"{c.contact_mailinglist.name}@{settings.GSUITE_DOMAIN}"
                for c in Society.objects.exclude(
                    contact_mailinglist=None
                ).select_related("contact_mailinglist")
            ],
            "moderated": True,
        },
        {
            "name": "newsletter",
            "description": "Automatic moderated mailinglist that can be used to send newsletters",
            "addresses": _get_members_email_addresses(
                Member.current_members.all().filter(profile__receive_newsletter=True)
            ),
            "moderated": True,
        },
    ]

    all_previous_board_members = []

    for board in Board.objects.filter(since__year__lte=lectureyear).order_by(
        "since__year"
    ):
        board_members = [
            board.member
            for board in MemberGroupMembership.objects.filter(
                group=board
            ).prefetch_related("member")
        ]
        all_previous_board_members += board_members
        years = str(board.since.year)[-2:] + str(board.until.year)[-2:]
        lists.append(
            {
                "name": f"board{years}",
                "aliases": [f"bestuur{years}"],
                "description": "Automatic mailinglist to send email to all board "
                f"members of {board.since.year}-{board.until.year}",
                "addresses": _get_members_email_addresses(board_members),
                "moderated": False,
            }
        )

    lists.append(
        {
            "name": "oldboards",
            "aliases": ["oudbesturen"],
            "description": "Automatic mailinglist to send "
            "email to all previous board members",
            "moderated": True,
            "addresses": _get_members_email_addresses(all_previous_board_members),
        }
    )

    return lists


def _get_members_email_addresses(members):
    return_list = []
    for member in members:
        for email in get_member_email_addresses(member):
            if email:
                return_list.append(email)
    return list(set(return_list))


def get_member_email_addresses(member):
    if member.is_staff and member.profile.email_gsuite_only:
        return [
            f"{member.username}@{settings.GSUITE_MEMBERS_DOMAIN}",
        ]
    if member.is_staff:
        return [
            member.email,
            f"{member.username}@{settings.GSUITE_MEMBERS_DOMAIN}",
        ]
    return [member.email]
