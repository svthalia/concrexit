"""The routes defined by the members package"""
from django.urls import path, include
from django.views.generic import RedirectView

from members.api.calendarjs.views import CalendarJSBirthdayListView
from members.views import (
    MembersIndex,
    StatisticsView,
    ProfileDetailView,
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
                path("profile/", ProfileDetailView.as_view(), name="profile"),
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
                    "change-email/",
                    include(
                        [
                            path(
                                "verify/<uuid:key>/",
                                EmailChangeVerifyView.as_view(),
                                name="email-change-verify",
                            ),
                            path(
                                "confirm/<uuid:key>/",
                                EmailChangeConfirmView.as_view(),
                                name="email-change-confirm",
                            ),
                            path(
                                "", EmailChangeFormView.as_view(), name="email-change"
                            ),
                        ]
                    ),
                ),
                path(
                    "",
                    RedirectView.as_view(
                        pattern_name="members:profile", permanent=True
                    ),
                    name="user",
                ),
            ]
        ),
    ),
    path(
        "api/calendarjs/",
        include(
            [
                path(
                    "birthdays/",
                    CalendarJSBirthdayListView.as_view(),
                    name="calendarjs-birthdays",
                ),
            ]
        ),
    ),
]
