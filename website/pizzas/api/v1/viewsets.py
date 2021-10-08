from django.db import IntegrityError
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from payments.api.v1.fields import PaymentTypeField
from payments.services import delete_payment, create_payment
from pizzas.models import Product, FoodEvent, FoodOrder
from pizzas.services import can_change_order

from . import serializers


class PizzaViewset(GenericViewSet, ListModelMixin):
    queryset = Product.available_products.all()
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.PizzaSerializer

    def list(self, request, *args, **kwargs):
        if FoodEvent.current() or request.user.has_perm("pizzas.change_product"):
            queryset = self.get_queryset()
            if not request.user.has_perm("pizzas.order_restricted_products"):
                queryset = queryset.exclude(restricted=True)
            serializer = serializers.PizzaSerializer(queryset, many=True)
            return Response(serializer.data)
        raise PermissionDenied

    @action(detail=False)
    def event(self, request):
        event = FoodEvent.current()

        if event:
            context = {"request": request}
            serializer = serializers.PizzaEventSerializer(event, context=context)
            return Response(serializer.data)

        raise NotFound


class OrderViewset(ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = FoodOrder.objects.all()

    def get_queryset(self):
        event = FoodEvent.current()
        if can_change_order(self.request.member, event):
            return FoodOrder.objects.filter(food_event=event)
        if self.action == "update" or self.action == "destroy":
            if not event or event.has_ended:
                return FoodOrder.objects.none()

            return FoodOrder.objects.filter(
                member=self.request.member, payment=None, food_event=event,
            )
        return FoodOrder.objects.filter(member=self.request.member, food_event=event)

    def get_serializer_class(self):
        event = FoodEvent.current()
        if can_change_order(self.request.member, event):
            return serializers.AdminOrderSerializer
        return serializers.OrderSerializer

    def get_object(self):
        if self.kwargs.get(self.lookup_field) == "me":
            order = get_object_or_404(
                self.get_queryset(),
                member=self.request.member,
                food_event=FoodEvent.current(),
            )
            self.check_object_permissions(self.request, order)
            return order
        return super().get_object()

    def perform_create(self, serializer):
        try:
            if serializer.validated_data.get("name"):
                serializer.save(food_event=FoodEvent.current())
            else:
                if can_change_order(self.request.member, FoodEvent.current()):
                    order = serializer.save(food_event=FoodEvent.current())
                    if "payment" in serializer.validated_data:
                        payment_type = serializer.validated_data["payment"]["type"]
                    else:
                        payment_type = PaymentTypeField.NO_PAYMENT

                    self._update_payment(order, payment_type, self.request.user)
                else:
                    serializer.save(
                        member=self.request.member, food_event=FoodEvent.current()
                    )
        except IntegrityError as e:
            raise ValidationError(
                "Something went wrong when saving the order" + str(e)
            ) from e

    def perform_update(self, serializer):
        order = serializer.save()
        if "payment" in serializer.validated_data and can_change_order(
            self.request.member, FoodEvent.current()
        ):
            self._update_payment(
                order, serializer.validated_data["payment"]["type"], self.request.user,
            )

    @staticmethod
    def _update_payment(order, payment_type=None, processed_by=None):
        if order.payment and payment_type == PaymentTypeField.NO_PAYMENT:
            delete_payment(order, processed_by)
        elif payment_type != PaymentTypeField.NO_PAYMENT:
            order.payment = create_payment(order, processed_by, payment_type)
            order.save()
