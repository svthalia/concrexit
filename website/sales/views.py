from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import DeleteView, DetailView
from django.views.generic.edit import FormView

from sales import services
from sales.forms import ProductOrderForm
from sales.models.order import Order, OrderItem, Shift


@method_decorator(login_required, name="dispatch")
class ShiftDetailView(DetailView):
    model = Shift
    context_object_name = "shift"
    template_name = "sales/shift_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shift = context["shift"]
        queryset = Order.objects.filter(shift=shift).order_by("-created_at")
        queryset = queryset.select_properties(
            "total_amount", "subtotal", "num_items", "age_restricted"
        )
        queryset = queryset.prefetch_related(
            "shift", "shift__event", "shift__product_list"
        )
        queryset = queryset.prefetch_related(
            "order_items", "order_items__product", "order_items__product__product"
        )
        queryset = queryset.prefetch_related("payment")
        context["orders"] = queryset.filter(
            Q(payer=self.request.member) | Q(created_by=self.request.member)
        )
        return context


@method_decorator(login_required, name="dispatch")
class PlaceOrderView(FormView):
    template_name = "sales/order_place.html"

    def dispatch(self, request, *args, **kwargs):
        self.shift = get_object_or_404(Shift, pk=kwargs["pk"])
        if not self.shift.selforder:
            # Orders can only be placed by shift managers
            # which is done through the admin.
            # Time issues are dealt with in the template.
            raise PermissionDenied
        if not self.shift.user_orders_allowed and request.method == "POST":
            # Forbid POSTing when not in the correct time period
            raise PermissionDenied
        if self.shift.locked:
            # You cannot order in a locked shift!
            raise PermissionDenied
        if not request.member.can_attend_events:
            raise PermissionDenied
        # TODO: if a shift belongs to an event, should we restrict self-ordering to event participants?
        # (at least if the event requires registration, of course)
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        return ProductOrderForm(
            self.shift.product_list,
            services.is_adult(self.request.member),
            **self.get_form_kwargs(),
        )

    @transaction.atomic
    def form_valid(self, form):
        order = Order(
            created_at=timezone.now(),
            created_by=self.request.member,
            shift=self.shift,
            payment=None,
            discount=0.00,
            payer=self.request.member,
        )
        order.save()
        for fieldname, amount in form.cleaned_data.items():
            if amount is None:
                continue
            if (
                not services.is_adult(self.request.member)
                and form.fields[fieldname].get_productlistitem().product.age_restricted
            ):
                raise PermissionDenied
            item = OrderItem(
                product=form.fields[fieldname].get_productlistitem(),
                order=order,
                amount=amount,
            )
            item.save()
        return redirect("sales:shift-detail", pk=self.shift.pk)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["shift"] = self.shift
        ctx["date_now"] = timezone.now()
        return ctx


@method_decorator(login_required, name="dispatch")
class CancelOrderView(DeleteView):
    model = Order

    def get_object(self, queryset=None):
        order = super().get_object(queryset)
        if not order.shift.user_orders_allowed:
            raise PermissionDenied
        if order.payment:
            raise PermissionDenied
        if order.created_by != self.request.member:
            raise PermissionDenied
        return order

    def get_success_url(self):
        return redirect("sales:shift-detail", pk=self.object.shift.pk)


@method_decorator(login_required, name="dispatch")
class OrderPaymentView(View):
    def get(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=kwargs["pk"])
        if order.payment:
            messages.warning(request, _("This order was already paid for."))
            return redirect("index")
        if order.payer is not None and order.payer != request.member:
            messages.warning(request, _("This order is not yours."))
            return redirect("index")

        order.payer = request.member
        order.save()

        if order.age_restricted and not services.is_adult(request.member):
            messages.error(
                request,
                _(
                    "The age restrictions on this order do not allow you to pay for this order."
                ),
            )
            return redirect("index")

        if (
            order.age_restricted
            and services.is_adult(request.member)
            and order.total_amount == 0
        ):
            messages.success(
                request, _("You have successfully identified yourself for this order.")
            )
            return redirect("index")

        if order.total_amount == 0:
            messages.info(request, _("This order doesn't require payment."))
            return redirect("index")

        return render(request, "sales/order_payment.html", {"order": order})
