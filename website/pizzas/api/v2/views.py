from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
    get_object_or_404,
    CreateAPIView,
    DestroyAPIView,
    UpdateAPIView,
)

from rest_framework import filters as framework_filters, status
from rest_framework.response import Response

from payments.exceptions import PaymentError
from payments.services import delete_payment
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
    queryset = FoodEvent.objects.all()
    filter_backends = (
        framework_filters.OrderingFilter,
        filters.FoodEventDateFilterBackend,
    )
    ordering_fields = ("start", "end")
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
    ]
    required_scopes = ["food:read"]


class FoodEventDetailView(RetrieveAPIView):
    """Returns one single food event."""

    serializer_class = FoodEventSerializer
    queryset = FoodEvent.objects.all()
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
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
    ]
    required_scopes = ["food:read"]


class FoodEventOrderDetailView(
    RetrieveAPIView, CreateAPIView, UpdateAPIView, DestroyAPIView
):
    """Returns details of a food order."""

    permission_classes = [
        IsAuthenticatedOrTokenHasScopeForMethod,
    ]
    required_scopes_per_method = {
        "GET": ["food:read"],
        "POST": ["food:order"],
        "PUT": ["food:order"],
        "PATCH": ["food:order"],
        "DELETE": ["food:order"],
    }

    def get_serializer_class(self):
        if self.request.method.lower() == "get":
            return FoodOrderSerializer
        if self.request.method.lower() == "post":
            return FoodOrderCreateSerializer
        return FoodOrderUpdateSerializer

    def get_queryset(self):
        return FoodOrder.objects.filter(food_event=self.food_event)

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        obj = get_object_or_404(queryset, member=self.request.member)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def dispatch(self, request, *args, **kwargs):
        self.food_event = get_object_or_404(FoodEvent, pk=self.kwargs.get("pk"))
        try:
            return super().dispatch(request, *args, **kwargs)
        except PaymentError as e:
            return Response(str(e), status=status.HTTP_403_FORBIDDEN,)

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        instance = self.get_object()

        if instance.payment:
            delete_payment(instance, member=request.member, ignore_change_window=True)

        return Response(
            FoodOrderSerializer(instance, context=self.get_serializer_context()).data
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            FoodOrderSerializer(
                serializer.instance, context=self.get_serializer_context()
            ).data,
            status=status.HTTP_201_CREATED,
        )
