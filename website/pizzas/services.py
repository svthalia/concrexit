from events.services import is_organiser
from . models import Product, Order, PizzaEvent


def gen_stats_pizza_orders():
    total = {}

    for product in Product.objects.all():
        total.update({
             product.name: Order.objects.filter(product=product).count(),
        })

    return {
        i[0]: i[1]
        for i in sorted(total.items(), key=lambda x: x[1], reverse=True)[:5]
        if i[1] > 0
    }


def gen_stats_current_pizza_orders():
    total = {}

    current_pizza_event = PizzaEvent.current()
    if not current_pizza_event:
        return None

    for product in Product.objects.filter():
        total.update({
            product.name: Order.objects.filter(
                product=product,
                pizza_event=current_pizza_event,
            ).count(),
        })

    return {
        i[0]: i[1]
        for i in sorted(total.items(), key=lambda x: x[1], reverse=True)[:5]
        if i[1] > 0
    }


def can_change_order(member, pizza_event):
    return (pizza_event and member.has_perm('pizzas.change_order') and
            is_organiser(member, pizza_event.event))
