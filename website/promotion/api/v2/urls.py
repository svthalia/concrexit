from django.urls import path

from promotion.api.v2.views import PromotionRequestListView, PromotionRequestUpdateView

app_name = "promotion"

urlpatterns = [
    path(
        "promotion/requests/",
        PromotionRequestListView.as_view(),
        name="promotion-requests",
    ),
    path(
        "promotion/requests/<int:pk>/",
        PromotionRequestUpdateView.as_view(),
        name="promotion-request",
    ),
]
