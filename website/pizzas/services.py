from events.services import is_organiser
from . models import Product, Order, PizzaEvent


def gen_stats_pizza_orders():
    total = []

    for product in Product.objects.all():
        total.append({
            'name': product.name,
            'total': Order.objects.filter(product=product).count(),
        })

    total.sort(key=lambda prod: prod['total'], reverse=True)

    return total


def gen_stats_current_pizza_orders():
    total = []

    current_pizza_event = PizzaEvent.current()
    if not current_pizza_event:
        return None

    for product in Product.objects.filter():
        total.append({
            'name': product.name,
            'total': Order.objects.filter(
                product=product,
                pizza_event=current_pizza_event,
            ).count(),
        })

    total.sort(key=lambda prod: prod['total'], reverse=True)

    return total


def can_change_order(member, pizza_event):
    return (pizza_event and member.has_perm('pizzas.change_order') and
            is_organiser(member, pizza_event.event))
