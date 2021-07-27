from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import filters as framework_filters
from rest_framework.generics import get_object_or_404

import pizzas.api.v2.filters as normal_filters
from pizzas.api.v2.admin.permissions import IsOrganiser
from pizzas.api.v2.admin.serializers.food_event import FoodEventAdminSerializer
from pizzas.api.v2.admin.serializers.order import FoodOrderAdminSerializer
from pizzas.api.v2.admin.serializers.product import ProductAdminSerializer
from pizzas.models import Product, FoodEvent, FoodOrder
from thaliawebsite.api.v2.admin import (
    AdminListAPIView,
    AdminCreateAPIView,
    AdminRetrieveAPIView,
    AdminUpdateAPIView,
    AdminDestroyAPIView,
)


class FoodEventAdminListView(AdminListAPIView, AdminCreateAPIView):
    """Returns an overview of all food events."""

    serializer_class = FoodEventAdminSerializer
    queryset = FoodEvent.objects.all()
    filter_backends = (
        framework_filters.OrderingFilter,
        normal_filters.FoodEventDateFilterBackend,
    )
    ordering_fields = ("start", "end")
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
    ]
    required_scopes = ["food:admin"]


class FoodEventAdminDetailView(AdminRetrieveAPIView, AdminUpdateAPIView):
    """Returns or updates one single food event."""

    serializer_class = FoodEventAdminSerializer
    queryset = FoodEvent.objects.all()
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
    ]
    required_scopes = ["food:admin"]


class ProductsAdminListView(AdminListAPIView, AdminCreateAPIView):
    """Returns an overview of all products."""

    permission_classes = [IsAuthenticatedOrTokenHasScope]
    serializer_class = ProductAdminSerializer
    queryset = Product.objects.all()
    filter_backends = [
        framework_filters.SearchFilter,
        normal_filters.FoodEventDateFilterBackend,
    ]
    search_fields = ("name",)
    required_scopes = ["food:admin"]


class ProductAdminDetailAPIView(
    AdminRetrieveAPIView, AdminUpdateAPIView, AdminDestroyAPIView
):
    """Returns details of one product."""

    queryset = Product.objects.all()
    serializer_class = ProductAdminSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["food:admin"]


class FoodEventOrdersAdminListView(AdminListAPIView, AdminCreateAPIView):
    """Returns a list of food orders."""

    serializer_class = FoodOrderAdminSerializer
    permission_classes = [IsAuthenticatedOrTokenHasScope]
    required_scopes = ["food:admin"]
    filter_backends = (
        framework_filters.OrderingFilter,
        framework_filters.SearchFilter,
    )
    ordering_fields = ("product", "payment", "member__first_name", "member__last_name")
    search_fields = (
        "product__name",
        "member__first_name",
        "member__last_name",
        "name",
    )

    def get_queryset(self):
        event = get_object_or_404(FoodEvent, pk=self.kwargs.get("pk"))
        if event:
            return FoodOrder.objects.filter(food_event_id=event).prefetch_related(
                "member", "member__profile", "food_event"
            )
        return FoodOrder.objects.none()


class FoodOrderAdminDetailView(
    AdminRetrieveAPIView, AdminUpdateAPIView, AdminDestroyAPIView
):
    """Returns details of a food order."""

    serializer_class = FoodOrderAdminSerializer
    queryset = FoodOrder.objects.all()
    permission_classes = [IsOrganiser, IsAuthenticatedOrTokenHasScope]
    required_scopes = ["food:admin"]
    event_lookup_field = "event_id"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(food_event_id=self.kwargs["event_id"])
            .prefetch_related("member", "member__profile", "food_event")
        )
