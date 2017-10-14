from django.shortcuts import get_object_or_404
from django.db import IntegrityError

from rest_framework import permissions
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework.mixins import ListModelMixin
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework.exceptions import (ValidationError, NotFound,
                                       PermissionDenied)

from pizzas.models import Product, PizzaEvent, Order
from pizzas.api import serializers


class PizzaViewset(GenericViewSet, ListModelMixin):
    queryset = Product.objects.filter(available=True)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.PizzaSerializer

    def list(self, request, *args, **kwargs):
        if (PizzaEvent.current() or
                request.user.has_perm('pizzas.change_product')):
            return super().list(request, *args, **kwargs)
        raise PermissionDenied

    @list_route()
    def event(self, request):
        event = PizzaEvent.current()

        if event:
            serializer = serializers.PizzaEventSerializer(event)
            return Response(serializer.data)

        raise NotFound


class OrderViewset(ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Order.objects.all()

    def get_queryset(self):
        event = PizzaEvent.current()
        if self.request.user.has_perm('pizzas.change_order'):
            return Order.objects.filter(pizza_event=event)
        if self.action == 'update' or self.action == 'destroy':
            if not event or event.has_ended:
                return Order.objects.none()

            return Order.objects.filter(member=self.request.member,
                                        paid=False,
                                        pizza_event=event)
        return Order.objects.filter(member=self.request.member,
                                    pizza_event=event)

    def get_serializer_class(self):
        if self.request.member.has_perm('pizzas.change_order'):
            return serializers.AdminOrderSerializer
        return serializers.OrderSerializer

    def get_object(self):
        if self.kwargs[self.lookup_field] == 'me':
            order = get_object_or_404(self.get_queryset(),
                                      member=self.request.member,
                                      pizza_event=PizzaEvent.current())
            self.check_object_permissions(self.request, order)
            return order
        return super().get_object()

    def perform_create(self, serializer):
        try:
            if serializer.validated_data.get('name'):
                serializer.save(pizza_event=PizzaEvent.current())
            else:
                if self.request.user.has_perm('pizzas.change_order'):
                    serializer.save(pizza_event=PizzaEvent.current())
                else:
                    serializer.save(member=self.request.member,
                                    pizza_event=PizzaEvent.current())
        except IntegrityError:
            raise ValidationError('Something went wrong when saving the order')
