"""The services defined by the mailinglists package"""

from django.conf import settings
from django.utils import timezone

from activemembers.models import MemberGroupMembership, Mentorship, Board
from members.models import Member, Membership
from utils.snippets import datetime_to_lectureyear


def get_automatic_lists():
    """Return list of mailing lists that should be generated automatically."""
    current_committee_chairs = (MemberGroupMembership.active_objects
                                .filter(group__board=None)
                                .filter(group__society=None)
                                .filter(chair=True)
                                .prefetch_related('member'))
    committee_chair_emails = [x.member for x in current_committee_chairs] + [
        Member(email='intern@thalia.nu')
    ]

    current_society_chairs = (MemberGroupMembership.active_objects
                              .filter(group__board=None)
                              .filter(group__committee=None)
                              .filter(chair=True)
                              .prefetch_related('member'))
    society_chair_emails = [x.member for x in current_society_chairs] + [
        Member(email='intern@thalia.nu')
    ]

    active_committee_memberships = (MemberGroupMembership.active_objects
                                    .filter(group__board=None)
                                    .filter(group__society=None)
                                    .prefetch_related('member'))

    active_members = [x.member for x in active_committee_memberships]

    lectureyear = datetime_to_lectureyear(timezone.now())
    # Change to next lecture year after December
    if 0 < timezone.now().month < 9:
        lectureyear += 1
    active_mentorships = Mentorship.objects.filter(
        year=lectureyear).prefetch_related('member')
    mentors = [x.member for x in active_mentorships]

    lists = []

    lists += _create_automatic_list(
        ['members', 'leden'], '[THALIA]',
        Member.all_with_membership('member'), '', True, True, True)
    lists += _create_automatic_list(
        ['benefactors', 'begunstigers'],
        '[THALIA]',
        Member.all_with_membership(Membership.BENEFACTOR), '',
        multilingual=True)
    lists += _create_automatic_list(
        ['honorary', 'ereleden'], '[THALIA]', Member.all_with_membership(
            'honorary'), '', multilingual=True)
    lists += _create_automatic_list(
        ['mentors'], '[THALIA] [MENTORS]', mentors, '', moderated=False)
    lists += _create_automatic_list(
        ['activemembers'], '[THALIA] [COMMITTEES]',
        active_members, '')
    lists += _create_automatic_list(
        ['committeechairs', 'commissievoorzitters'], '[THALIA] [CHAIRS]',
        committee_chair_emails, '', moderated=False)
    lists += _create_automatic_list(
        ['societychairs', 'gezelschapvoorzitters'], '[THALIA] [SOCIETY]',
        society_chair_emails, '', moderated=False)
    lists += _create_automatic_list(
        ['optin'], '[THALIA] [OPTIN]', Member.current_members.filter(
            profile__receive_optin=True), '', multilingual=True)

    all_previous_board_members = []

    for board in Board.objects.filter(
            since__year__lte=lectureyear).order_by('since__year'):
        board_members = [board.member for board in
                         MemberGroupMembership.objects.filter
                         (group=board).prefetch_related('member')]
        all_previous_board_members += board_members
        lists += _create_automatic_list(
            ['bestuur'
             + str(board.since.year)[-2:] + str(board.until.year)[-2:],
             'board'
             + str(board.since.year)[-2:] + str(board.until.year)[-2:]],
            '',
            board_members,
            archived=False, moderated=False, multilingual=False
        )

    lists += _create_automatic_list(
        ['oldboards', 'oudbesturen'], '',
        all_previous_board_members
    )

    return lists


def _create_automatic_list(names, prefix, members, description='',
                           archived=True, moderated=True, multilingual=False):
    data = {
        'names': names,
        'name': names[0],
        'description': description,
        'aliases': names[1:],
        'prefix': prefix,
        'archived': archived,
        'moderated': moderated,
    }

    if multilingual:
        data['addresses'] = set([member.email for member in members
                                 if member.email])
        yield data  # this is the complete list, e.g. leden@
        for language in settings.LANGUAGES:
            localized_data = data.copy()
            localized_data['addresses'] = [
                member.email for member in members
                if member.profile.language == language[0] and member.email]
            localized_data['names'] = [
                '{}-{}'.format(n, language[0]) for n in names]
            localized_data['name'] = localized_data['names'][0]
            localized_data['aliases'] = localized_data['names'][1:]
            yield localized_data  # these are localized lists, e.g. leden-nl@
    else:
        data['addresses'] = set([member.email for member in members
                                 if member.email])
        yield data
