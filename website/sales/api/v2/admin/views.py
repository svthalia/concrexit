from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import exceptions
from rest_framework import filters as framework_filters
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import DjangoModelPermissions

from sales.api.v2 import filters
from sales.api.v2.admin.permissions import IsManager
from sales.api.v2.admin.serializers.order import OrderListSerializer, OrderSerializer
from sales.api.v2.admin.serializers.shift import ShiftSerializer
from sales.models.order import Order
from sales.models.shift import Shift
from thaliawebsite.api.v2.admin import (
    AdminCreateAPIView,
    AdminDestroyAPIView,
    AdminListAPIView,
    AdminRetrieveAPIView,
    AdminUpdateAPIView,
)


class ShiftListView(AdminListAPIView):
    """Returns an overview of all sales shifts."""

    serializer_class = ShiftSerializer
    queryset = Shift.objects.all()
    filter_backends = (
        framework_filters.OrderingFilter,
        framework_filters.SearchFilter,
        filters.ShiftActiveFilter,
        filters.ShiftLockedFilter,
        filters.ShiftDateFilter,
    )
    ordering_fields = ("start", "end")
    permission_classes = [IsAuthenticatedOrTokenHasScope, DjangoModelPermissions]
    required_scopes = ["sales:admin"]

    def get_queryset(self):
        queryset = super().get_queryset().filter(locked=False)

        if not self.request.member:
            queryset = queryset.none()
        elif not self.request.member.has_perm("sales.override_manager"):
            queryset = queryset.filter(
                managers__in=self.request.member.get_member_groups()
            ).distinct()

        queryset = queryset.select_properties(
            "active",
            "total_revenue",
            "total_revenue_paid",
            "num_orders",
            "num_orders_paid",
        )
        queryset = queryset.prefetch_related("event", "product_list")
        queryset = queryset.prefetch_related(
            "orders__order_items",
        )
        return queryset


class ShiftDetailView(AdminRetrieveAPIView):
    serializer_class = ShiftSerializer
    queryset = Shift.objects.all()
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
        DjangoModelPermissions,
        IsManager,
    ]
    required_scopes = ["sales:admin"]


class OrderListView(AdminListAPIView, AdminCreateAPIView):
    method_serializer_classes = {
        ("GET",): OrderListSerializer,
        ("POST",): OrderSerializer,
    }
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
        DjangoModelPermissions,
        IsManager,
    ]
    required_scopes = ["sales:admin"]
    shift_lookup_field = "pk"

    def get_serializer_class(self):
        for methods, serializer_cls in self.method_serializer_classes.items():
            if self.request.method in methods:
                return serializer_cls
        raise exceptions.MethodNotAllowed(self.request.method)

    def create(self, request, *args, **kwargs):
        shift = Shift.objects.get(pk=kwargs["pk"])
        if shift.locked:
            raise PermissionDenied

        return super().create(request, args, kwargs)

    def perform_create(self, serializer):
        serializer.save(created_by_id=self.request.member.pk)

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
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        pk = self.kwargs.get("pk")
        if pk:
            shift = get_object_or_404(Shift, pk=self.kwargs.get("pk"))
            context.update({"shift": shift})
        return context


class OrderDetailView(AdminRetrieveAPIView, AdminUpdateAPIView, AdminDestroyAPIView):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
        DjangoModelPermissions,
        IsManager,
    ]
    required_scopes = ["sales:admin"]

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
        return queryset
