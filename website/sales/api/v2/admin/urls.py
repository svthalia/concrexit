from django.urls import path

from sales.api.v2.admin.views import (
    ShiftListView,
    ShiftDetailView,
    OrderListView,
    OrderDetailView,
)

app_name = "sales"

urlpatterns = [
    path("sales/shifts/", ShiftListView.as_view(), name="shift-list"),
    path(
        "sales/shifts/<int:pk>/",
        ShiftDetailView.as_view(),
        name="shift-detail",
    ),
    path(
        "sales/shifts/<int:pk>/orders/",
        OrderListView.as_view(),
        name="shift-orders",
    ),
    path(
        "sales/orders/<uuid:pk>/",
        OrderDetailView.as_view(),
        name="order-detail",
    ),
]
