from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseRedirect, JsonResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import permission_required
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required

from .models import Product, PizzaEvent, Order
from .forms import AddOrderForm


@login_required
def index(request):
    products = Product.objects.filter(available=True)
    event = PizzaEvent.current()
    try:
        order = Order.objects.get(pizza_event=event,
                                  member=request.user.member)
    except Order.DoesNotExist:
        order = None
    context = {'event': event, 'products': products, 'order': order}
    return render(request, 'pizzas/index.html', context)


@permission_required('pizzas.change_order')
def orders(request, event_pk):
    event = get_object_or_404(PizzaEvent, pk=event_pk)
    context = {'event': event,
               'orders': Order.objects.filter(pizza_event=event)
                                      .prefetch_related('member', 'product')}
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

    context = {
        'event': event,
        'product_list': product_list,
        'total_money': total_money,
        'total_products': total_products
    }

    return render(request, 'pizzas/overview.html', context)


@require_http_methods(["POST"])
@permission_required('pizzas.change_order')
def toggle_orderpayment(request):
    if 'order' not in request.POST:
        return JsonResponse({'error': _("You must supply an order pk.")})
    try:
        order = get_object_or_404(Order, pk=int(request.POST['order']))
    except Http404:
        return JsonResponse({'error': _("Order not found!")})
    order.paid = not order.paid
    order.save()
    return JsonResponse({'success': 1, 'paid': int(order.paid)})


@require_http_methods(["POST"])
@permission_required('pizzas.change_order')
def delete_order(request):
    if 'order' in request.POST:
        try:
            order = get_object_or_404(Order, pk=int(request.POST['order']))
            order.delete()
        except Http404:
            pass  # TODO use contrib.messages for some information here
    event = PizzaEvent.current()
    if event:
        return HttpResponseRedirect(reverse('pizzas:orders', args=[event.pk]))
    return HttpResponseRedirect(reverse('pizzas:index'))


@require_http_methods(["POST"])
def cancel_order(request):
    if 'order' in request.POST:
        try:
            order = get_object_or_404(Order, pk=int(request.POST['order']))
            if order.member == request.user.member:
                order.delete()
        except Http404:
            pass  # TODO use contrib.messages for some information here
    # TODO use contrib.messages for some information here
    return HttpResponseRedirect(reverse('pizzas:index'))


@permission_required('pizzas.change_order')
def add_order(request, event_pk):
    event = get_object_or_404(PizzaEvent, pk=event_pk)
    if request.POST:
        form = AddOrderForm(request.POST)
        order = form.save(commit=False)
        order.pizza_event = event
        order.save()
        # TODO use contrib.messages for some information here
        return HttpResponseRedirect(reverse('pizzas:orders', args=[event.pk]))
    context = {
        'event': event,
        'form': AddOrderForm(),
    }
    return render(request, 'pizzas/add_order.html', context)


@login_required
def order(request):
    if 'product' in request.POST:
        product = Product.objects.get(pk=int(request.POST['product']))
        if product:
            event = PizzaEvent.current()
            try:
                order = Order.objects.get(pizza_event=event,
                                          member=request.user.member)
            except Order.DoesNotExist:
                order = Order(pizza_event=event, member=request.user.member)
            order.product = product
            order.save()
    return HttpResponseRedirect(reverse('pizzas:index'))
