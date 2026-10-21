from django.urls import path

from sales.views import (
    CancelOrderView,
    OrderPaymentView,
    PlaceOrderView,
    ShiftDetailView,
)

app_name = "sales"

urlpatterns = [
    path(
        "sales/shifts/<int:pk>/",
        ShiftDetailView.as_view(),
        name="shift-detail",
    ),
    path(
        "sales/shifts/<int:pk>/order",
        PlaceOrderView.as_view(),
        name="order-place",
    ),
    path(
        "sales/order/<uuid:pk>/pay/",
        OrderPaymentView.as_view(),
        name="order-pay",
    ),
    path(
        "sales/order/<uuid:pk>/cancel/",
        CancelOrderView.as_view(),
        name="order-cancel",
    ),
]
