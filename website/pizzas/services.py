from events.services import is_organiser
from .models import Product, FoodOrder


def gen_stats_pizza_orders() -> dict:
    """Generate statistics about number of orders per product."""
    data = {"labels": [], "datasets": [{"data": []},]}

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
