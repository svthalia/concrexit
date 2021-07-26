from django.urls import path, include

from . import views

app_name = "partners"

urlpatterns = [
    path(
        "career/",
        include(
            [
                path("", views.index, name="index"),
                path("partners/<slug>/", views.partner, name="partner"),
                path("vacancies", views.vacancies, name="vacancies"),
            ]
        ),
    ),
]
