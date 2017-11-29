from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods

from .forms import AddOrderForm
from .models import Order, PizzaEvent, Product


@login_required
def index(request):
    products = Product.objects.filter(available=True).order_by('name')
    event = PizzaEvent.current()
    try:
        order = Order.objects.get(pizza_event=event,
                                  member=request.member)
    except Order.DoesNotExist:
        order = None
    context = {'event': event, 'products': products, 'order': order}
    return render(request, 'pizzas/index.html', context)


@permission_required('pizzas.change_order')
def orders(request, event_pk):
    event = get_object_or_404(PizzaEvent, pk=event_pk)
    context = {'event': event,
               'orders': Order.objects.filter(pizza_event=event)
                                      .prefetch_related('member', 'product')
                                      .order_by('member__first_name')}
    return render(request, 'pizzas/orders.html', context)


@permission_required('pizzas.change_order')
def overview(request, event_pk):
    event = get_object_or_404(PizzaEvent, pk=event_pk)

    product_list = {}
    total_money = 0
    total_products = 0
    orders = Order.objects.filter(pizza_event=event)\
                          .prefetch_related('product')

    for order in orders:
        if order.product.id not in product_list:
            product_list[order.product.id] = {
                'name': order.product.name,
                'price': order.product.price,
                'amount': 0,
                'total': 0
            }
        product_list[order.product.id]['amount'] += 1
        product_list[order.product.id]['total'] += order.product.price
        total_products += 1
        total_money += order.product.price

    product_list = sorted(product_list.values(), key=lambda x: x['name'])

    context = {
        'event': event,
        'product_list': product_list,
        'total_money': total_money,
        'total_products': total_products
    }

    return render(request, 'pizzas/overview.html', context)


@require_http_methods(["POST"])
@permission_required('pizzas.change_order')
def delete_order(request):
    if 'order' in request.POST:
        try:
            order = get_object_or_404(Order, pk=int(request.POST['order']))
            order.delete()
        except Http404:
            messages.error(request, _("Your order could not be found."))
    event = PizzaEvent.current()
    if event:
        return HttpResponseRedirect(reverse('pizzas:orders', args=[event.pk]))
    return HttpResponseRedirect(reverse('pizzas:index'))


@require_http_methods(["POST"])
def cancel_order(request):
    if 'order' in request.POST:
        try:
            order = get_object_or_404(Order, pk=int(request.POST['order']))
            if not order.can_be_changed:
                messages.error(request,
                               _('You can no longer cancel.'))
            elif order.member == request.member:
                order.delete()
                messages.success(request, _("Your order has been cancelled."))
        except Http404:
            messages.error(request, _("Your order could not be found."))
    return HttpResponseRedirect(reverse('pizzas:index'))


@permission_required('pizzas.change_order')
def add_order(request, event_pk):
    event = get_object_or_404(PizzaEvent, pk=event_pk)
    if request.POST:
        form = AddOrderForm(request.POST)
        order = form.save(commit=False)
        order.pizza_event = event
        order.save()
        messages.success(request, _("Your order was successful."))
        return HttpResponseRedirect(reverse('pizzas:orders', args=[event.pk]))
    context = {
        'event': event,
        'form': AddOrderForm(),
    }
    return render(request, 'pizzas/add_order.html', context)


@login_required
def order(request):
    event = PizzaEvent.current()
    if not event:
        return HttpResponseRedirect(reverse('pizzas:index'))

    try:
        order_placed = Order.objects.get(pizza_event=event,
                                         member=request.member)
        current_order_locked = not order_placed.can_be_changed
    except Order.DoesNotExist:
        current_order_locked = False

    if 'product' in request.POST and not current_order_locked:
        product = Product.objects.get(pk=int(request.POST['product']))
        if product:
            try:
                order = Order.objects.get(pizza_event=event,
                                          member=request.member)
            except Order.DoesNotExist:
                order = Order(pizza_event=event, member=request.member)
            order.product = product
            order.save()
    return HttpResponseRedirect(reverse('pizzas:index'))
