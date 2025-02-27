from django.urls import path
from django.views.generic import RedirectView

from partners.api.v2.views import (
    PartnerDetailView,
    PartnerListView,
    VacancyCategoryListView,
    VacancyDetailView,
    VacancyListView,
)

app_name = "partners"

urlpatterns = [
    path(
        "partners/events/",
        RedirectView.as_view(
            pattern_name="api:v2:events:external-events-list",
            permanent=False,
            query_string=True,
        ),
        name="partner-events-list",
    ),
    path(
        "partners/events/<int:pk>/",
        RedirectView.as_view(
            pattern_name="api:v2:events:external-event-detail",
            permanent=False,
            query_string=True,
        ),
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
