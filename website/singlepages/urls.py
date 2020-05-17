"""Defines the routes provided in this package"""
from django.urls import path, include

from .views import (
    PrivacyPolicyView,
    EventTermsView,
    SiblingAssociationsView,
    BecomeActiveView,
    StyleGuideView,
    ContactView,
)

app_name = "singlepages"

urlpatterns = [
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
                )
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
