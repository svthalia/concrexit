"""Events app API v2 urls."""
from django.urls import path

from events.api.v2.admin.views import EventRegistrationAdminFieldsView
from pizzas.api.v2.admin.views import (
    FoodEventAdminListView,
    FoodEventAdminDetailView,
    FoodOrderAdminDetailView,
    FoodEventOrdersAdminListView,
    ProductsAdminListView,
    ProductAdminDetailAPIView,
)

app_name = "food"

urlpatterns = [
    path("food/events/", FoodEventAdminListView.as_view(), name="food-events-index"),
    path(
        "food/events/<int:pk>/",
        FoodEventAdminDetailView.as_view(),
        name="food-event-detail",
    ),
    path(
        "food/events/<int:pk>/orders/",
        FoodEventOrdersAdminListView.as_view(),
        name="food-event-orders",
    ),
    path(
        "food/events/<int:event_id>/orders/<int:pk>/",
        FoodOrderAdminDetailView.as_view(),
        name="food-event-order-detail",
    ),
    path("food/products/", ProductsAdminListView.as_view(), name="food-products-index"),
    path(
        "food/products/<int:pk>/",
        ProductAdminDetailAPIView.as_view(),
        name="food-product-detail",
    ),
]
