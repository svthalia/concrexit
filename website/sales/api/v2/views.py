from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
    CreateAPIView,
    UpdateAPIView,
    DestroyAPIView,
)
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly

from sales.api.v2.admin.serializers.order import OrderSerializer, OrderListSerializer
from sales.api.v2.admin.views import (
    OrderListView,
    OrderDetailView,
    ShiftDetailView,
    ShiftListView,
)
from sales.api.v2.serializers.user_order import UserOrderSerializer
from sales.api.v2.serializers.user_shift import UserShiftSerializer
from sales.models.shift import SelfOrderPeriod, Shift
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
        return queryset.filter(payer=self.request.member)


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
        return queryset.filter(payer=self.request.member)

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
        return super(UserOrderDetailView, self).destroy(request, *args, **kwargs)
