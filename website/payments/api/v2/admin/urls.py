"""Payments app API v2 urls."""
from django.urls import path

from payments.api.v2.admin.views import (
    PaymentListCreateView,
    PaymentDetailView,
    PayableDetailView,
)

app_name = "payments"

urlpatterns = [
    path("payments/", PaymentListCreateView.as_view(), name="payments-list"),
    path("payments/<uuid:pk>/", PaymentDetailView.as_view(), name="payment-detail"),
    path(
        "payments/payables/<str:app_label>/<str:model_name>/<str:payable_pk>/",
        PayableDetailView.as_view(),
        name="payments-payable-detail",
    ),
]
