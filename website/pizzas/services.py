from django.utils import timezone

from events.services import is_organiser
from .models import Product, FoodOrder


def gen_stats_pizza_orders() -> dict:
    """Generate statistics about number of orders per product."""
    data = {
        "labels": [],
        "datasets": [
            {"data": []},
        ],
    }

    for product in Product.objects.all():

        orders = FoodOrder.objects.filter(product=product).count()

        if orders > 0:
            data["labels"].append(product.name)
            data["datasets"][0]["data"].append(orders)

    return data


def can_change_order(member, food_event):
    """Determine if a certain member can edit orders of an event.

    :param member: Member who wants to change and order
    :param food_event: The event for which we want to change an order
    :return: True if we can change an order else False
    """
    return (
        food_event
        and member.has_perm("pizzas.change_foodorder")
        and is_organiser(member, food_event.event)
    )


def execute_data_minimisation(dry_run=False):
    """Anonymizes pizzas orders older than 3 years."""
    # Sometimes years are 366 days of course, but better delete 1 or 2 days early than late
    deletion_period = timezone.now().date() - timezone.timedelta(days=(365 * 3))

    queryset = FoodOrder.objects.filter(food_event__end__lte=deletion_period).exclude(
        name="<removed>"
    )
    if not dry_run:
        queryset.update(member=None, name="<removed>")
    return queryset
