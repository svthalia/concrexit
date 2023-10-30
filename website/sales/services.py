import datetime

from django.utils import timezone

from activemembers.models import Board
from sales.models.order import Order
from sales.models.product import ProductList
from sales.models.shift import Shift


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


def create_daily_merchandise_sale_shift():
    today = timezone.now().date()
    merchandise_product_list = ProductList.objects.get_or_create(
        name="Merchandise Product List"
    )[0]
    active_board = Board.objects.filter(since__lte=today, until__gte=today)

    shift = Shift.objects.create(
        title="Merchandise sales",
        start=timezone.now(),
        end=timezone.datetime.combine(today, datetime.time(23, 59, 59)),
        product_list=merchandise_product_list,
    )
    shift.managers.set(active_board)
    shift.save()


def lock_merchandise_sale_shift():
    shifts = Shift.objects.filter(title="Merchandise sales").all()
    for shift in shifts:
        if shift.num_orders == 0:
            shift.delete()
        else:
            shift.locked = True
            shift.save()


def renew_merchandise_sale_shift():
    lock_merchandise_sale_shift()
    create_daily_merchandise_sale_shift()
