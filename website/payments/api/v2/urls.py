from django.urls import path

from payments.api.v2.views import (
    PayableDetailView,
    PaymentDetailView,
    PaymentListView,
    PaymentUserCurrentView,
)

app_name = "payments"

urlpatterns = [
    path("payments/", PaymentListView.as_view(), name="payments-list"),
    path(
        "payments/users/me/",
        PaymentUserCurrentView.as_view(),
        name="payments-tpay-status",
    ),
    path("payments/<uuid:pk>/", PaymentDetailView.as_view(), name="payment-detail"),
    path(
        "payments/payables/<str:app_label>/<str:model_name>/<str:payable_pk>/",
        PayableDetailView.as_view(),
        name="payments-payable-detail",
    ),
]
