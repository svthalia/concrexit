from django.db.models import Count, Q
from django.utils import timezone

from activemembers.models import Committee


def generate_statistics() -> dict:
    """Generate statistics about number of members in each committee."""
    committees = Committee.active_objects.annotate(
        member_count=(
            Count(
                "members",
                filter=(
                    Q(membergroupmembership__until=None)
                    | Q(membergroupmembership__until__gte=timezone.now())
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
