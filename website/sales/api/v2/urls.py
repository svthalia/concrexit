from django.urls import path

from sales.api.v2.views import (
    OrderClaimView,
    UserShiftListView,
    UserShiftDetailView,
    UserOrderListView,
    UserOrderDetailView,
)

app_name = "sales"

urlpatterns = [
    path("sales/order/<uuid:pk>/claim/", OrderClaimView.as_view(), name="order-claim"),
    path("sales/shifts/", UserShiftListView.as_view(), name="user-shift-list"),
    path(
        "sales/shifts/<int:pk>/",
        UserShiftDetailView.as_view(),
        name="user-shift-detail",
    ),
    path(
        "sales/shifts/<int:pk>/orders/",
        UserOrderListView.as_view(),
        name="user-order-list",
    ),
    path(
        "sales/orders/<uuid:pk>/",
        UserOrderDetailView.as_view(),
        name="user-order-detail",
    ),
]
