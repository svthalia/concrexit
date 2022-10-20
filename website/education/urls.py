"""The routes defined by the education package."""
from django.conf.urls import include
from django.urls import path
from django.views.generic.base import RedirectView

from education.views import (
    BookInfoView,
    CourseDetailView,
    CourseIndexView,
    ExamCreateView,
    ExamDetailView,
    StudentParticipantView,
    SummaryCreateView,
    SummaryDetailView,
)

app_name = "education"

urlpatterns = [
    path(
        "education/",
        include(
            [
                path("books/", BookInfoView.as_view(), name="books"),
                path(
                    "courses/",
                    include(
                        [
                            path(
                                "<int:pk>/",
                                include(
                                    [
                                        path(
                                            "exam/upload/",
                                            ExamCreateView.as_view(),
                                            name="submit-exam",
                                        ),
                                        path(
                                            "summary/upload/",
                                            SummaryCreateView.as_view(),
                                            name="submit-summary",
                                        ),
                                        path(
                                            "",
                                            CourseDetailView.as_view(),
                                            name="course",
                                        ),
                                    ]
                                ),
                            ),
                            path(
                                "exam/<int:pk>/", ExamDetailView.as_view(), name="exam"
                            ),
                            path(
                                "summary/<int:pk>/",
                                SummaryDetailView.as_view(),
                                name="summary",
                            ),
                            path(
                                "exam/upload/",
                                ExamCreateView.as_view(),
                                name="submit-exam",
                            ),
                            path(
                                "summary/upload/",
                                SummaryCreateView.as_view(),
                                name="submit-summary",
                            ),
                            path("", CourseIndexView.as_view(), name="courses"),
                        ]
                    ),
                ),
                path(
                    "student-participation/",
                    StudentParticipantView.as_view(),
                    name="student-participation",
                ),
                path(
                    "",
                    RedirectView.as_view(
                        pattern_name="education:courses", permanent=True
                    ),
                    name="index",
                ),
            ]
        ),
    ),
]
