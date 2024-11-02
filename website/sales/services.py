from django.db.models import Sum
from django.utils import timezone

from sales.models.order import Order, OrderItem


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
                .exists()
            )
        )
    return False


def execute_data_minimisation(dry_run=False):
    """Anonymizes orders older than 3 years."""
    # Sometimes years are 366 days of course, but better delete 1 or 2 days early than late
    deletion_period = timezone.now().date() - timezone.timedelta(days=365 * 3)

    queryset = Order.objects.filter(created_at__lte=deletion_period).exclude(
        payer__isnull=True
    )
    if not dry_run:
        queryset.update(payer=None)
    return queryset.all()


def gen_stats_sales_orders() -> dict:
    """Generate statistics about number of orders per product."""
    data = {
        "labels": [],
        "datasets": [
            {"data": []},
        ],
    }

    for product, count in (
        OrderItem.objects.values("product_name")
        .annotate(count=Sum("amount"))
        .filter(count__gt=0)
        .order_by("-count")
        .values_list("product_name", "count")[:10]
    ):
        data["labels"].append(product)
        data["datasets"][0]["data"].append(count)

    return data
