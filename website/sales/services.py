from django.utils import timezone

from sales.models.order import Order


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


def execute_data_minimisation(dry_run=False):
    """Anonymizes orders older than 3 years."""
    # Sometimes years are 366 days of course, but better delete 1 or 2 days early than late
    deletion_period = timezone.now().date() - timezone.timedelta(days=(365 * 3))

    queryset = Order.objects.filter(created_at__lte=deletion_period).exclude(
        payer__isnull=True
    )
    if not dry_run:
        queryset.update(payer=None)
    return queryset.all()
