from django.urls import path

from sales.views import place_order_view, OrderPaymentView

app_name = "sales"

urlpatterns = [
    path(
        "sales/shifts/<int:pk>/order",
        place_order_view,
        name="order-place",
    ),
    path(
        "sales/order/<uuid:pk>/pay/",
        OrderPaymentView.as_view(),
        name="order-pay",
    ),
]
