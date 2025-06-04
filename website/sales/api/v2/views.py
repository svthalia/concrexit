from django.db.models import Q

from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import exceptions
from rest_framework import filters as framework_filters
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import (
    GenericAPIView,
    ListAPIView,
    CreateAPIView,
    RetrieveAPIView,
    UpdateAPIView,
    DestroyAPIView,
    get_object_or_404,
)
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema

from sales import services
from sales.api.v2 import filters
from sales.api.v2.admin.serializers.order import OrderListSerializer, OrderSerializer
from sales.api.v2.serializers.user_shift import UserShiftSerializer
from sales.models.order import Order
from sales.models.shift import Shift
from thaliawebsite.api.v2.permissions import IsAuthenticatedOrTokenHasScopeForMethod


class UserShiftListView(ListAPIView):
    serializer_class = UserShiftSerializer
    queryset = Shift.objects.filter(selforder=True)
    filter_backends = (
        framework_filters.OrderingFilter,
        framework_filters.SearchFilter,
        filters.ShiftActiveFilter,
        filters.ShiftLockedFilter,
        filters.ShiftDateFilter,
    )
    ordering_fields = ("start", "end")

    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
        DjangoModelPermissionsOrAnonReadOnly,
    ]
    required_scopes = ["sales:read"]


class UserShiftDetailView(RetrieveAPIView):
    serializer_class = UserShiftSerializer
    queryset = Shift.objects.filter(selforder=True)
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
        DjangoModelPermissionsOrAnonReadOnly,
    ]
    required_scopes = ["sales:read"]


class UserOrderListView(ListAPIView, CreateAPIView):
    permission_classes = [
        IsAuthenticatedOrTokenHasScopeForMethod,
    ]
    required_scopes_per_method = {
        "GET": ["sales:read"],
        "POST": ["sales:order"],
    }
    method_serializer_classes = {
        ("GET",): OrderListSerializer,
        ("POST",): OrderSerializer,
    }
    shift_lookup_field = "pk"

    def get_serializer_class(self):
        for methods, serializer_cls in self.method_serializer_classes.items():
            if self.request.method in methods:
                return serializer_cls
        raise exceptions.MethodNotAllowed(self.request.method)

    def create(self, request, *args, **kwargs):
        shift = Shift.objects.get(pk=kwargs["pk"])
        if not shift.user_orders_allowed:
            raise PermissionDenied
        if shift.locked:
            raise PermissionDenied
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(
            payer_id=self.request.member.pk, created_by_id=self.request.member.pk
        )

    def get_queryset(self):
        queryset = Order.objects.all()

        pk = self.kwargs.get("pk")
        if pk:
            queryset = queryset.filter(shift=pk)

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

        return queryset.filter(
            Q(payer=self.request.member) | Q(created_by=self.request.member)
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        pk = self.kwargs.get("pk")
        if pk:
            shift = get_object_or_404(Shift, pk=self.kwargs.get("pk"))
            context.update({"shift": shift})
        return context


class UserOrderDetailView(RetrieveAPIView, UpdateAPIView, DestroyAPIView):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
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
        queryset = super().get_queryset()

        if not self.request.member:
            queryset = queryset.none()
        elif not self.request.member.has_perm("sales.override_manager"):
            queryset = queryset.filter(
                shift__managers__in=self.request.member.get_member_groups()
            ).distinct()

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
        return queryset.filter(
            Q(payer=self.request.member) | Q(created_by=self.request.member)
        )

    def update(self, request, *args, **kwargs):
        if not self.get_object().shift.user_orders_allowed:
            raise PermissionDenied
        if self.get_object().payment:
            raise PermissionDenied
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not self.get_object().shift.user_orders_allowed:
            raise PermissionDenied
        if self.get_object().payment:
            raise PermissionDenied
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not self.get_object().shift.user_orders_allowed:
            raise PermissionDenied
        if self.get_object().payment:
            raise PermissionDenied
        return super().destroy(request, *args, **kwargs)


class OrderClaimView(GenericAPIView):
    """Claims an order to be paid by the current user."""

    class OrderClaimViewSchema(AutoSchema):
        def get_request_serializer(self, path, method):
            # This endpoint does not expect any content in the request body.
            return None

    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    schema = OrderClaimViewSchema(operation_id_base="claimOrder")
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["sales:order"]

    def patch(self, request, *args, **kwargs):
        if request.member is None:
            raise PermissionDenied(
                detail="You need to be a member to pay for an order."
            )

        order = self.get_object()
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

        serializer = self.get_serializer(order)
        return Response(serializer.data)
