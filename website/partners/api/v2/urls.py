"""Partners app API v2 urls."""
from django.urls import path

from partners.api.v2.views import (
    PartnerEventListView,
    PartnerListView,
    PartnerEventDetailView,
    PartnerDetailView,
    VacancyListView,
    VacancyDetailView,
    VacancyCategoryListView,
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
    path("partners/vacancies/", VacancyListView.as_view(), name="vacancies-list"),
    path(
        "partners/vacancies/categories/",
        VacancyCategoryListView.as_view(),
        name="vacancy-categories-list",
    ),
    path(
        "partners/vacancies/<int:pk>/",
        VacancyDetailView.as_view(),
        name="vacancies-detail",
    ),
    path("partners/", PartnerListView.as_view(), name="partners-list"),
    path("partners/<int:pk>/", PartnerDetailView.as_view(), name="partners-detail"),
]
