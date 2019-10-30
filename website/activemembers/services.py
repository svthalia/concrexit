from django.db.models import Count, Q
from django.utils import timezone

from activemembers.models import Committee


def generate_statistics():
    """
    Generate statistics about number of members in each committee
    :return: Dict with key, value being resp. name, member count of committees.
    """
    committees = Committee.active_objects.annotate(member_count=(
        Count('members', filter=(
            Q(membergroupmembership__until=None) |
            Q(membergroupmembership__until__gte=timezone.now())))))

    data = {}
    for committee in committees:
        data.update({
            committee.name: committee.member_count
        })

    return data
