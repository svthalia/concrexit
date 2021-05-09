from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
    get_object_or_404,
    CreateAPIView,
    DestroyAPIView,
    UpdateAPIView,
)

from rest_framework import filters as framework_filters, status
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from rest_framework.response import Response

from pizzas.api.v2 import filters
from pizzas.api.v2.serializers import (
    ProductSerializer,
    FoodOrderSerializer,
    FoodOrderUpdateSerializer,
    FoodOrderCreateSerializer,
)
from pizzas.api.v2.serializers.food_event import FoodEventSerializer
from pizzas.models import FoodEvent, Product, FoodOrder
from thaliawebsite.api.v2.permissions import IsAuthenticatedOrTokenHasScopeForMethod


class FoodEventListView(ListAPIView):
    """Returns an overview of all food events."""

    serializer_class = FoodEventSerializer
    queryset = FoodEvent.current_objects.all()
    filter_backends = (
        framework_filters.OrderingFilter,
        filters.FoodEventDateFilterBackend,
    )
    ordering_fields = ("start", "end")
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
        DjangoModelPermissionsOrAnonReadOnly,
    ]
    required_scopes = ["food:read"]


class FoodEventDetailView(RetrieveAPIView):
    """Returns one single food event."""

    serializer_class = FoodEventSerializer
    queryset = FoodEvent.current_objects.all()
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
        DjangoModelPermissionsOrAnonReadOnly,
    ]
    required_scopes = ["food:read"]


class FoodEventProductsListView(ListAPIView):
    """Returns an overview of all products."""

    serializer_class = ProductSerializer
    queryset = Product.available_products.all()
    filter_backends = (framework_filters.SearchFilter,)
    search_fields = ("name",)
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
        DjangoModelPermissionsOrAnonReadOnly,
    ]
    required_scopes = ["food:read"]


class FoodEventOrdersView(ListAPIView, CreateAPIView):
    """Returns a list of registrations."""

    permission_classes = [
        IsAuthenticatedOrTokenHasScopeForMethod,
        DjangoModelPermissionsOrAnonReadOnly,
    ]
    required_scopes_per_method = {
        "GET": ["food:read"],
        "POST": ["food:order"],
        "DELETE": ["food:order"],
    }

    def get_serializer_class(self):
        if self.request.method.lower() == "post":
            return FoodOrderCreateSerializer
        return FoodOrderSerializer

    def get_queryset(self):
        return FoodOrder.objects.filter(food_event=self.food_event.pk)

    def dispatch(self, request, *args, **kwargs):
        self.food_event = get_object_or_404(FoodEvent, pk=self.kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(food_event=self.food_event)
        return Response(
            FoodOrderSerializer(instance, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )


class FoodEventOrderDetailView(RetrieveAPIView, UpdateAPIView, DestroyAPIView):
    """Returns details of an event registration."""

    queryset = FoodOrder.objects.all()
    permission_classes = [
        IsAuthenticatedOrTokenHasScopeForMethod,
        DjangoModelPermissionsOrAnonReadOnly,
    ]
    required_scopes_per_method = {
        "GET": ["food:read"],
        "PUT": ["food:order"],
        "PATCH": ["food:order"],
        "DELETE": ["food:order"],
    }

    def get_serializer_class(self):
        if self.request.method.lower() == "get":
            return FoodOrderSerializer
        return FoodOrderUpdateSerializer

    def get_queryset(self):
        return super().get_queryset().filter(food_event=self.kwargs["event_pk"])

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        instance = self.get_object()
        return Response(
            FoodOrderSerializer(instance, context=self.get_serializer_context()).data
        )
