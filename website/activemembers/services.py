from django.db.models import Count, Q
from django.utils import timezone

from activemembers.models import Committee
from members.models.member import Member


def generate_statistics() -> dict:
    """Generate statistics about number of members in each committee."""
    now = timezone.now()
    committees = Committee.active_objects.annotate(
        member_count=(
            Count(
                "members",
                filter=(
                    Q(membergroupmembership__until=None)
                    | Q(
                        membergroupmembership__since__lte=now,
                        membergroupmembership__until__gte=now,
                    )
                ),
            )
        )
    )

    data = {
        "labels": [],
        "datasets": [
            {"data": []},
        ],
    }
    for committee in committees:
        data["labels"].append(committee.name)
        data["datasets"][0]["data"].append(committee.member_count)

    return data


def revoke_staff_permission_for_users_in_no_commitee():
    members = Member.objects.filter(is_staff=True)
    revoked = []
    for member in members:
        if not member.get_member_groups().exists() and not member.is_superuser:
            revoked.append(member.id)
            member.is_staff = False
            member.save()
    return Member.objects.filter(pk__in=revoked)
