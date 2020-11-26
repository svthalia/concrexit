from django.urls import path

from sales.views import OrderPaymentView

app_name = "sales"

urlpatterns = [
    path("sales/order/<uuid:pk>/pay/", OrderPaymentView.as_view(), name="order-pay",),
]
