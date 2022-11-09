"""Defines the routes provided in this package."""
from django.urls import include, path

from .views import (
    BecomeActiveView,
    ContactView,
    EventTermsView,
    PrivacyPolicyView,
    ResponsibleDisclosureView,
    SiblingAssociationsView,
    StudentParticipantView,
    StudentWellBeingView,
    StyleGuideView,
)

app_name = "singlepages"

urlpatterns = [
    path(
        "responsible-disclosure/",
        ResponsibleDisclosureView.as_view(),
        name="responsible-disclosure",
    ),
    path("privacy-policy/", PrivacyPolicyView.as_view(), name="privacy-policy"),
    path(
        "event-registration-terms/",
        EventTermsView.as_view(),
        name="event-registration-terms",
    ),
    path(
        "association/",
        include(
            [
                path(
                    "sibling-associations/",
                    SiblingAssociationsView.as_view(),
                    name="sibling-associations",
                ),
            ]
        ),
    ),
    path(
        "education/",
        include(
            [
                path(
                    "student-well-being/",
                    StudentWellBeingView.as_view(),
                    name="student-well-being",
                ),
                path(
                    "student-participation/",
                    StudentParticipantView.as_view(),
                    name="student-participation",
                ),
            ]
        ),
    ),
    path(
        "members/",
        include(
            [
                path(
                    "become-active/", BecomeActiveView.as_view(), name="become-active"
                ),
                path("styleguide/", StyleGuideView.as_view(), name="styleguide"),
            ]
        ),
    ),
    path("contact", ContactView.as_view(), name="contact"),
]
