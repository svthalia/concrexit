from django.urls import path

from sales.views import (
    OrderPaymentView,
    PlaceOrderView,
    ShiftDetailView,
    cancel_order_view,
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
        cancel_order_view,
        name="order-cancel",
    ),
]
