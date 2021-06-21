from events.services import is_organiser
from .models import Product, FoodOrder, FoodEvent


def gen_stats_pizza_orders():
    """Generate statistics about number of orders per product.

    :return: Dict with key, value being resp. name, order count of a product.
    """
    total = {}

    for product in Product.objects.all():
        total.update(
            {product.name: FoodOrder.objects.filter(product=product).count(),}
        )

    return {
        i[0]: i[1]
        for i in sorted(total.items(), key=lambda x: x[1], reverse=True)[:5]
        if i[1] > 0
    }


def gen_stats_current_pizza_orders():
    """Generate statistics about number of orders per product of the active pizza event.

    :return: Dict with key, value being resp. name, order count of a product.
    """
    total = {}

    current_pizza_event = FoodEvent.current()
    if not current_pizza_event:
        return None

    for product in Product.objects.filter():
        total.update(
            {
                product.name: FoodOrder.objects.filter(
                    product=product, food_event=current_pizza_event,
                ).count(),
            }
        )

    return {
        i[0]: i[1]
        for i in sorted(total.items(), key=lambda x: x[1], reverse=True)[:5]
        if i[1] > 0
    }


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
