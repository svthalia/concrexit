import django.contrib.admin.models
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import filters, exceptions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
    get_object_or_404,
    RetrieveUpdateDestroyAPIView,
    ListCreateAPIView,
)
from rest_framework.permissions import DjangoModelPermissions

from sales.api.v2.serializers.order import OrderSerializer, OrderListSerializer
from sales.api.v2.serializers.shift import ShiftSerializer
from sales.models.order import Order
from sales.models.shift import Shift
from thaliawebsite.api.v2.permissions import IsAuthenticatedOrTokenHasScopeForMethod


class ShiftListView(ListAPIView):
    """Returns an overview of all sales shifts."""

    serializer_class = ShiftSerializer
    queryset = Shift.objects.all()
    filter_backends = (
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    ordering_fields = ("start", "end")
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
        DjangoModelPermissions,
    ]
    required_scopes = ["sales:read"]

    def get_queryset(self):
        queryset = super().get_queryset().filter(locked=False)

        if not (
            self.request.member.is_superuser
            or self.request.member.has_perm("sales.override_manager")
        ):
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
        queryset = queryset.prefetch_related("orders__order_items",)
        return queryset


class ShiftDetailView(RetrieveAPIView):
    serializer_class = ShiftSerializer
    queryset = Shift.objects.all()
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
        DjangoModelPermissions,
    ]
    required_scopes = ["sales:read"]

    def retrieve(self, request, *args, **kwargs):
        if not Shift.objects.get(pk=kwargs["pk"]).is_manager(self.request.member):
            raise PermissionDenied
        return super(ShiftDetailView, self).retrieve(request, args, kwargs)


class OrderListView(ListCreateAPIView):
    method_serializer_classes = {
        ("GET",): OrderListSerializer,
        ("POST",): OrderSerializer,
    }
    permission_classes = [
        IsAuthenticatedOrTokenHasScopeForMethod,
        DjangoModelPermissions,
    ]
    required_scopes_per_method = {
        "GET": ["sales:read"],
        "POST": ["sales:write"],
    }

    def get_serializer_class(self):
        for methods, serializer_cls in self.method_serializer_classes.items():
            if self.request.method in methods:
                return serializer_cls
        raise exceptions.MethodNotAllowed(self.request.method)

    def list(self, request, *args, **kwargs):
        if not Shift.objects.get(pk=kwargs["pk"]).is_manager(self.request.member):
            raise PermissionDenied
        return super(OrderListView, self).list(request, args, kwargs)

    def create(self, request, *args, **kwargs):
        shift = Shift.objects.get(pk=kwargs["pk"])
        if shift.locked:
            raise PermissionDenied

        if not shift.is_manager(self.request.member):
            raise PermissionDenied

        response = super(OrderListView, self).create(request, args, kwargs)
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(Order).pk,
            object_id=response.data["pk"],
            object_repr=f"Order {response.data['pk']}",
            action_flag=django.contrib.admin.models.ADDITION,
            change_message=f"Created order (API){': ' if response.data['order_description'] else ''}{response.data['order_description']}",
        )
        return response

    def get_queryset(self):
        queryset = Order.objects

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
        context = super(OrderListView, self).get_serializer_context()
        pk = self.kwargs.get("pk")
        if pk:
            shift = get_object_or_404(Shift, pk=self.kwargs.get("pk"))
            context.update({"shift": shift})
        return context


class OrderDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    permission_classes = [
        IsAuthenticatedOrTokenHasScopeForMethod,
        DjangoModelPermissions,
    ]
    required_scopes_per_method = {
        "GET": ["sales:read"],
        "PATCH": ["sales:write"],
        "PUT": ["sales:write"],
        "DELETE": ["sales:write"],
    }

    def retrieve(self, request, *args, **kwargs):
        if not Order.objects.get(pk=kwargs["pk"]).shift.is_manager(self.request.member):
            raise PermissionDenied
        return super(OrderDetailView, self).retrieve(request, args, kwargs)

    def update(self, request, *args, **kwargs):
        try:
            order_pk = kwargs["pk"]
        except KeyError:
            order_pk = args[1]["pk"]

        if not Order.objects.get(pk=order_pk).shift.is_manager(self.request.member):
            raise PermissionDenied

        response = super(OrderDetailView, self).update(request, args, kwargs)
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(Order).pk,
            object_id=response.data["pk"],
            object_repr=f"Order {response.data['pk']}",
            action_flag=django.contrib.admin.models.CHANGE,
            change_message=f"Updated order (API){': ' if response.data['order_description'] else ''}{response.data['order_description']}",
        )
        return response

    def partial_update(self, request, *args, **kwargs):
        if not Order.objects.get(pk=kwargs["pk"]).shift.is_manager(self.request.member):
            raise PermissionDenied
        return super(OrderDetailView, self).partial_update(request, args, kwargs)

    def delete(self, request, *args, **kwargs):
        if not Order.objects.get(pk=kwargs["pk"]).shift.is_manager(self.request.member):
            raise PermissionDenied
        return super(OrderDetailView, self).delete(request, args, kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()

        if not (
            self.request.member.is_superuser
            or self.request.member.has_perm("sales.override_manager")
        ):
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
