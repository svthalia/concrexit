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


def is_organiser(member, pizza_event):
    if member and member.is_authenticated:
        if member.is_superuser or member.has_perm('events.override_organiser'):
            return True

        if pizza_event:
            return member.get_member_groups().filter(
                    pk=pizza_event.event.organiser.pk).count() != 0

    return False


def can_change_order(member, pizza_event):
    return (member.has_perm('pizzas.change_order') and
            is_organiser(member, pizza_event))
