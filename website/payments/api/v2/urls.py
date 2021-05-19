"""Payments app API v2 urls."""
from django.urls import path

from payments.api.v2.views import PaymentListCreateView, PaymentDetailView

urlpatterns = [
    path("payments/", PaymentListCreateView.as_view(), name="payments-list"),
    path("payments/<uuid:pk>/", PaymentDetailView.as_view(), name="payment-detail"),
]
