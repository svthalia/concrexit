from activemembers.models import CommitteeMembership
from members.models import Member
from thaliawebsite.settings import settings


def get_automatic_lists():
    memberships = (CommitteeMembership.active_memberships
                   .filter(committee__board=None)
                   .filter(chair=True)
                   .prefetch_related('member__user'))
    committee_chairs = [x.member for x in memberships]

    # name, prefix, members, archived, moderated, multilingual

    lists = [
        ('leden', '[THALIA]', Member.all_with_membership(
            'member', 'user'), True, True, True),
        ('begunstigers', '[THALIA]', Member.all_with_membership(
            'supporter', 'user'), True, True, True),
        ('ereleden', '[THALIA]', Member.all_with_membership(
            'honorary', 'user'), True, True, True),
        ('members', '[THALIA]', Member.all_with_membership(
            'member', 'user'), True, True, True),
        ('supporters', '[THALIA]', Member.all_with_membership(
            'supporter', 'user'), True, True, True),
        ('honorary', '[THALIA]', Member.all_with_membership(
            'honorary', 'user'), True, True, True),
        ('commissievoorzitters', '[THALIA] [VOORZITTERS]',
            committee_chairs, True, False, False),
        ('optin', '[THALIA] [OPTIN]', Member.active_members.filter(
            receive_optin=True).prefetch_related('user'), True, True, False),
    ]

    return_data = []
    for list in lists:
        data = {
            'name': list[0],
            'prefix': list[1],
            'archived': list[3],
            'moderated': list[4],
        }

        if list[5]:
            data['addresses'] = (member.user.email for member in list[2])
            return_data.append(data)
            for language in settings.LANGUAGES:
                localized_data = data.copy()
                localized_data['addresses'] = [
                    member.user.email for member in list[2]
                    if member.language == language[0]]
                localized_data['name'] += '-{}'.format(language[0])
                return_data.append(localized_data)
        else:
            data['addresses'] = (member.user.email for member in list[2])
            return_data.append(data)

    return return_data
