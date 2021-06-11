from django.utils import timezone


def is_adult(member):
    today = timezone.now().date()
    return member.profile.birthday <= today.replace(year=today.year - 18)


def is_manager(member, shift):
    if member and member.is_authenticated:
        return (
            member.is_superuser
            or member.has_perm("sales.override_manager")
            or (
                member.get_member_groups()
                .filter(pk__in=shift.managers.values_list("pk"))
                .count()
                != 0
            )
        )
    return False
