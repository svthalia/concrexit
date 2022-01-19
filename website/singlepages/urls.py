"""Defines the routes provided in this package."""
from django.urls import path, include

from .views import (
    ResponsibleDisclosureView,
    PrivacyPolicyView,
    EventTermsView,
    SiblingAssociationsView,
    BecomeActiveView,
    StyleGuideView,
    ContactView,
    TrustContactPersonsView,
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
                path(
                    "trust-contacts/",
                    TrustContactPersonsView.as_view(),
                    name="trust-contacts",
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
