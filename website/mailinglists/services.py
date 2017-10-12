from django.contrib.auth.models import User
from django.utils import timezone

from activemembers.models import CommitteeMembership, Mentorship
from members.models import Member
from thaliawebsite.settings import settings
from utils.snippets import datetime_to_lectureyear


def get_automatic_lists():
    memberships = (CommitteeMembership.active_memberships
                   .filter(committee__board=None)
                   .filter(chair=True)
                   .prefetch_related('member__user'))
    committee_chairs = [x.member.member for x in memberships] + [Member(
        user=User(
            email='intern@thalia.nu'
        )
    )]

    active_committee_memberships = (CommitteeMembership.active_memberships
                                    .exclude(committee__board__is_board=True)
                                    .prefetch_related('member__member'))
    active_members = [x.member.member for x in active_committee_memberships]

    lectureyear = datetime_to_lectureyear(timezone.now())
    # Change to next lecture year after December
    if 0 < timezone.now().month < 9:
        lectureyear += 1
    active_mentorships = Mentorship.objects.filter(
        year=lectureyear)
    mentors = [x.member.member for x in active_mentorships]

    lists = []

    lists += _create_automatic_list(
        ['leden', 'members'], '[THALIA]',
        Member.all_with_membership('member', 'user'), True, True, True)
    lists += _create_automatic_list(
        ['begunstigers', 'supporters'], '[THALIA]', Member.all_with_membership(
            'supporter', 'user'), multilingual=True)
    lists += _create_automatic_list(
        ['ereleden', 'honorary'], '[THALIA]', Member.all_with_membership(
            'honorary', 'user'), multilingual=True)
    lists += _create_automatic_list(
        ['mentors'], '[THALIA] [MENTORS]', mentors, moderated=False)
    lists += _create_automatic_list(
        ['activemembers'], '[THALIA] [COMMITTEES]',
        active_members)
    lists += _create_automatic_list(
        ['commissievoorzitters', 'committeechairs'], '[THALIA] [CHAIRS]',
        committee_chairs, moderated=False)
    lists += _create_automatic_list(
        ['optin'], '[THALIA] [OPTIN]', Member.active_members.filter(
            receive_optin=True).prefetch_related('user'), multilingual=True)

    return lists


def _create_automatic_list(names, prefix, members,
                           archived=True, moderated=True, multilingual=False):
    data = {
        'names': names,
        'prefix': prefix,
        'archived': archived,
        'moderated': moderated,
    }

    if multilingual:
        data['addresses'] = [member.user.email for member in members]
        yield data  # this is the complete list, e.g. leden@
        for language in settings.LANGUAGES:
            localized_data = data.copy()
            localized_data['addresses'] = [
                member.user.email for member in members
                if member.language == language[0]]
            localized_data['names'] = [
                '{}-{}'.format(n, language[0]) for n in names]
            yield localized_data  # these are localized lists, e.g. leden-nl@
    else:
        data['addresses'] = [member.user.email for member in members]
        yield data
