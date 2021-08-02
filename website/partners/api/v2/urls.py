"""Partners app API v2 urls."""
from django.urls import path

from partners.api.v2.views import (
    PartnerEventListView,
    PartnerListView,
    PartnerEventDetailView,
)

app_name = "partners"

urlpatterns = [
    path(
        "partners/events/", PartnerEventListView.as_view(), name="partner-events-list"
    ),
    path(
        "partners/events/<int:pk>/",
        PartnerEventDetailView.as_view(),
        name="partner-events-detail",
    ),
    path("partners/", PartnerListView.as_view(), name="partners-list"),
]
