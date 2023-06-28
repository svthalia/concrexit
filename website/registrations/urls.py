"""The routes defined by the registrations package."""
from django.urls import include, path
from django.views.generic import TemplateView

from .views import (
    BecomeAMemberView,
    BenefactorRegistrationFormView,
    ConfirmEmailView,
    EntryAdminView,
    MemberRegistrationFormView,
    NewYearForStudylong,
    ReferenceCreateView,
    RenewalFormView,
)

app_name = "registrations"

urlpatterns = [
    path(
        "registration/",
        include(
            [
                path(
                    "admin/process/<uuid:pk>/",
                    EntryAdminView.as_view(),
                    name="admin-process",
                ),
                path(
                    "confirm-email/<uuid:pk>/",
                    ConfirmEmailView.as_view(),
                    name="confirm-email",
                ),
                path(
                    "reference/<uuid:pk>/",
                    ReferenceCreateView.as_view(),
                    name="reference",
                ),
                path(
                    "reference/<uuid:pk>/success",
                    ReferenceCreateView.as_view(success=True),
                    name="reference-success",
                ),
            ]
        ),
    ),
    path(
        "user/membership/",
        include(
            [
                path("", RenewalFormView.as_view(), name="renew"),
                path("renew/studylong/", NewYearForStudylong.as_view(), name="newYear"),
                path(
                    "renew/success/",
                    TemplateView.as_view(
                        template_name="registrations/renewal_success.html"
                    ),
                    name="renew-success",
                ),
                path(
                    "renew/completed/",
                    TemplateView.as_view(
                        template_name="registrations/renewal_completed.html"
                    ),
                    name="renewal-completed",
                ),
            ]
        ),
    ),
    path(
        "association/",
        include(
            [
                path("register/", BecomeAMemberView.as_view(), name="index"),
                path(
                    "register/member/",
                    MemberRegistrationFormView.as_view(),
                    name="register-member",
                ),
                path(
                    "register/benefactor/",
                    BenefactorRegistrationFormView.as_view(),
                    name="register-benefactor",
                ),
                path(
                    "register/success/",
                    TemplateView.as_view(
                        template_name="registrations/register_success.html"
                    ),
                    name="register-success",
                ),
            ]
        ),
    ),
]
