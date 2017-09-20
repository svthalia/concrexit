from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404
from django.db import IntegrityError

from rest_framework import permissions
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework.mixins import ListModelMixin
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

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
        return Response(status=403)

    @list_route()
    def event(self, request):
        event = PizzaEvent.current()

        if event:
            try:
                order = Order.objects.get(pizza_event=event,
                                          member=request.user.member)
                return JsonResponse({
                    'event': serializers.PizzaEventSerializer(event).data,
                    'order': serializers.OrderSerializer(order).data
                })
            except Order.DoesNotExist:
                return JsonResponse({
                    'event': serializers.PizzaEventSerializer(event).data,
                    'order': None
                })

        return JsonResponse({
            'event': None,
            'order': None,
        })


class OrderViewset(ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Order.objects.all()

    def get_queryset(self):
        event = PizzaEvent.current()
        if self.request.user.has_perm('pizzas.change_order'):
            return Order.objects.filter(pizza_event=event)
        if self.action == 'update':
            if not event or event.has_ended:
                return Order.objects.none()

            return Order.objects.filter(member=self.request.user.member,
                                        paid=False,
                                        pizza_event=event)
        return Order.objects.filter(member=self.request.user.member,
                                    pizza_event=event)

    def get_serializer_class(self):
        if self.request.user.has_perm('pizzas.change_order'):
            return serializers.AdminOrderSerializer
        return serializers.OrderSerializer

    def get_object(self):
        if self.kwargs[self.lookup_field] == 'me':
            order = get_object_or_404(Order,
                                      member=self.request.user.member,
                                      pizza_event=PizzaEvent.current())
            self.check_object_permissions(self.request, order)
            return order
        return super().get_object()

    # def create(self, request, *args, **kwargs):
    def perform_create(self, serializer):
        try:
            if serializer.validated_data.get('name'):
                print(serializer.validated_data.get('name'))
                serializer.save(pizza_event=PizzaEvent.current())
            else:
                serializer.save(member=self.request.user.member,
                                pizza_event=PizzaEvent.current())
        except IntegrityError:
            raise ValidationError('Something went wrong when saving the order')
