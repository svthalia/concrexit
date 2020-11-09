from django.db import IntegrityError
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from payments.api.fields import PaymentTypeField
from payments.services import delete_payment, create_payment
from pizzas.api import serializers
from pizzas.models import Product, PizzaEvent, Order
from pizzas.services import can_change_order


class PizzaViewset(GenericViewSet, ListModelMixin):
    queryset = Product.available_products.all()
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.PizzaSerializer

    def list(self, request, *args, **kwargs):
        if PizzaEvent.current() or request.user.has_perm("pizzas.change_product"):
            queryset = self.get_queryset()
            if not request.user.has_perm("pizzas.order_restricted_products"):
                queryset = queryset.exclude(restricted=True)
            serializer = serializers.PizzaSerializer(queryset, many=True)
            return Response(serializer.data)
        raise PermissionDenied

    @action(detail=False)
    def event(self, request):
        event = PizzaEvent.current()

        if event:
            context = {"request": request}
            serializer = serializers.PizzaEventSerializer(event, context=context)
            return Response(serializer.data)

        raise NotFound


class OrderViewset(ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Order.objects.all()

    def get_queryset(self):
        event = PizzaEvent.current()
        if can_change_order(self.request.member, event):
            return Order.objects.filter(pizza_event=event)
        if self.action == "update" or self.action == "destroy":
            if not event or event.has_ended:
                return Order.objects.none()

            return Order.objects.filter(
                member=self.request.member, payment=None, pizza_event=event,
            )
        return Order.objects.filter(member=self.request.member, pizza_event=event)

    def get_serializer_class(self):
        event = PizzaEvent.current()
        if can_change_order(self.request.member, event):
            return serializers.AdminOrderSerializer
        return serializers.OrderSerializer

    def get_object(self):
        if self.kwargs.get(self.lookup_field) == "me":
            order = get_object_or_404(
                self.get_queryset(),
                member=self.request.member,
                pizza_event=PizzaEvent.current(),
            )
            self.check_object_permissions(self.request, order)
            return order
        return super().get_object()

    def perform_create(self, serializer):
        try:
            if serializer.validated_data.get("name"):
                serializer.save(pizza_event=PizzaEvent.current())
            else:
                if can_change_order(self.request.member, PizzaEvent.current()):
                    order = serializer.save(pizza_event=PizzaEvent.current())
                    if "payment" in serializer.validated_data:
                        payment_type = serializer.validated_data["payment"]["type"]
                    else:
                        payment_type = PaymentTypeField.NO_PAYMENT

                    self._update_payment(order, payment_type, self.request.user)
                else:
                    serializer.save(
                        member=self.request.member, pizza_event=PizzaEvent.current()
                    )
        except IntegrityError as e:
            raise ValidationError(
                "Something went wrong when saving the order" + str(e)
            ) from e

    def perform_update(self, serializer):
        order = serializer.save()
        if "payment" in serializer.validated_data and can_change_order(
            self.request.member, PizzaEvent.current()
        ):
            self._update_payment(
                order, serializer.validated_data["payment"]["type"], self.request.user,
            )

    @staticmethod
    def _update_payment(order, payment_type=None, processed_by=None):
        if order.payment and payment_type == PaymentTypeField.NO_PAYMENT:
            delete_payment(order)
        else:
            order.payment = create_payment(order, processed_by, payment_type)
            order.save()
