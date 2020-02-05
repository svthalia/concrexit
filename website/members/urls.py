"""The routes defined by the members package"""
from django.urls import path, include

from members.views import (
    MembersIndex,
    StatisticsView,
    ProfileDetailView,
    UserAccountView,
    UserProfileUpdateView,
    EmailChangeFormView,
    EmailChangeVerifyView,
    EmailChangeConfirmView,
)

app_name = "members"

urlpatterns = [
    path(
        "members/",
        include(
            [
                path("statistics/", StatisticsView.as_view(), name="statistics"),
                path("profile/<int:pk>", ProfileDetailView.as_view(), name="profile"),
                path("directory/<slug:filter>/", MembersIndex.as_view(), name="index"),
                path("directory/", MembersIndex.as_view(), name="index"),
            ]
        ),
    ),
    path(
        "user/",
        include(
            [
                path(
                    "edit-profile/",
                    UserProfileUpdateView.as_view(),
                    name="edit-profile",
                ),
                path(
                    "change-email/verify/<uuid:key>/",
                    EmailChangeVerifyView.as_view(),
                    name="email-change-verify",
                ),
                path(
                    "change-email/confirm/<uuid:key>/",
                    EmailChangeConfirmView.as_view(),
                    name="email-change-confirm",
                ),
                path(
                    "change-email/", EmailChangeFormView.as_view(), name="email-change"
                ),
                path("", UserAccountView.as_view(), name="user"),
            ]
        ),
    ),
]
