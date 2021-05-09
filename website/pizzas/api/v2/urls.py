"""Pizzas app API v2 urls."""
from django.urls import path

from pizzas.api.v2.views import (
    FoodEventListView,
    FoodEventDetailView,
    FoodEventProductsListView,
    FoodEventOrderDetailView,
)

urlpatterns = [
    path("food/events/", FoodEventListView.as_view(), name="food-events-list"),
    path(
        "food/events/<int:pk>/", FoodEventDetailView.as_view(), name="food-event-detail"
    ),
    path(
        "food/events/<int:pk>/order",
        FoodEventOrderDetailView.as_view(),
        name="food-event-order-detail",
    ),
    path(
        "food/events/<int:event_pk>/products/",
        FoodEventProductsListView.as_view(),
        name="food-products-list",
    ),
]
