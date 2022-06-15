from django.db.models import Q
from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from rest_framework.response import Response
from rest_framework import status
from sales.api.v2.admin.serializers.order import OrderListSerializer, OrderSerializer
from sales.api.v2.admin.views import (
    OrderDetailView,
    OrderListView,
    ShiftDetailView,
    ShiftListView,
)
import sales.services as services
from sales.api.v2.serializers.user_order import UserOrderSerializer
from sales.api.v2.serializers.user_shift import UserShiftSerializer
from sales.models.shift import Shift
from sales.models.order import Order
from thaliawebsite.api.v2.permissions import IsAuthenticatedOrTokenHasScopeForMethod


class UserShiftListView(ShiftListView):
    serializer_class = UserShiftSerializer
    # queryset = SelfOrderPeriod.objects.all()
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
        DjangoModelPermissionsOrAnonReadOnly,
    ]
    required_scopes = ["sales:read"]


class UserShiftDetailView(ShiftDetailView):
    serializer_class = UserShiftSerializer
    # queryset = SelfOrderPeriod.objects.all()
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
        DjangoModelPermissionsOrAnonReadOnly,
    ]
    required_scopes = ["sales:read"]


class UserOrderListView(OrderListView):
    permission_classes = [
        IsAuthenticatedOrTokenHasScopeForMethod,
    ]
    required_scopes_per_method = {
        "GET": ["sales:read"],
        "POST": ["sales:order"],
    }
    method_serializer_classes = {
        ("GET",): OrderListSerializer,
        ("POST",): UserOrderSerializer,
    }

    def create(self, request, *args, **kwargs):
        shift = Shift.objects.get(pk=kwargs["pk"])
        if not shift.user_orders_allowed:
            raise PermissionDenied
        return super(UserOrderListView, self).create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(
            payer_id=self.request.member.pk, created_by_id=self.request.member.pk
        )

    def get_queryset(self):
        queryset = super(UserOrderListView, self).get_queryset()
        return queryset.filter(
            Q(payer=self.request.member) | Q(created_by=self.request.member)
        )


class UserOrderDetailView(OrderDetailView):
    serializer_class = UserOrderSerializer
    permission_classes = [
        IsAuthenticatedOrTokenHasScopeForMethod,
    ]
    required_scopes_per_method = {
        "GET": ["sales:read"],
        "PATCH": ["sales:order"],
        "PUT": ["sales:order"],
        "DELETE": ["sales:order"],
    }

    def get_queryset(self):
        queryset = super(UserOrderDetailView, self).get_queryset()
        return queryset.filter(
            Q(payer=self.request.member) | Q(created_by=self.request.member)
        )

    def update(self, request, *args, **kwargs):
        if not self.get_object().shift.user_orders_allowed:
            raise PermissionDenied
        if self.get_object().payment:
            raise PermissionDenied
        return super(UserOrderDetailView, self).update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not self.get_object().shift.user_orders_allowed:
            raise PermissionDenied
        if self.get_object().payment:
            raise PermissionDenied
        return super(UserOrderDetailView, self).partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not self.get_object().shift.user_orders_allowed:
            raise PermissionDenied
        if self.get_object().payment:
            raise PermissionDenied

class OrderPaymentView(APIView):
    """
    API endpoint that allows users to claim an order, even if user orders aren't allowed.

    This is the API equivalent of `sales.views.OrderPaymentView`.
    """

    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["sales:order"]

    def get_serializer_context(self):
        return {"request": self.request, "format": self.format_kwarg, "view": self}

    def get(self, request, *args, **kwargs):
        if request.member is None:
            raise PermissionDenied("You need to be a member to pay for an order.")

        order = get_object_or_404(Order, pk=kwargs["pk"])
        if order.payment:
            raise PermissionDenied(detail="This order was already paid for.")

        if order.payer is not None and order.payer != request.member:
            raise PermissionDenied(detail="This order is not yours.")

        order.payer = request.member
        order.save()

        if order.age_restricted and not services.is_adult(request.member):
            raise PermissionDenied(
                "The age restrictions on this order do not allow you to pay for this order."
            )

        serializer = UserOrderSerializer(
            instance=order,
            context=self.get_serializer_context(),
        )
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK,
            content_type="application/json",
        )
