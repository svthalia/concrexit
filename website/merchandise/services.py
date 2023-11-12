import datetime

from django.utils import timezone

from activemembers.models import Board
from merchandise.models import MerchandiseProduct
from sales.models.product import ProductList
from sales.models.shift import Shift


def update_merchandise_product_list():
    product_list = ProductList.objects.get_or_create(name="Merchandise")[0]
    merchandise_products = MerchandiseProduct.objects.all()

    for merchandise_product in merchandise_products:
        item, _ = product_list.product_items.get_or_create(
            product=merchandise_product,
            defaults={"price": merchandise_product.merchandise_item.price},
        )
        item.price = merchandise_product.merchandise_item.price
        item.save()

    return product_list


def create_daily_merchandise_sale_shift():
    today = timezone.now().date()
    merchandise_product_list = update_merchandise_product_list()
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
