"""Members app API v2 urls."""
from django.urls import path

from members.api.v2.views import MemberListView, MemberDetailView

urlpatterns = [
    path("members/", MemberListView.as_view(), name="member-list"),
    path("members/<int:pk>/", MemberDetailView.as_view(), name="member-detail",),
]
