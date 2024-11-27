"""API v2 views of the announcements app."""

from announcements.api.v2.serializers import (
    AnnouncementSerializer,
    FrontpageArticleSerializer,
    SlideSerializer,
)
from announcements.context_processors import announcements
from announcements.models import FrontpageArticle, Slide
from announcements.services import close_announcement
from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import viewsets
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response


class AnnouncementsAPIViewMixin:
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
    ]
    required_scopes = ["announcements:read"]


class SlideListView(AnnouncementsAPIViewMixin, ListAPIView):
    """Returns an overview of all slides that are currently active."""

    serializer_class = SlideSerializer
    queryset = Slide.visible_objects.order_by("order")


class SlideDetailView(AnnouncementsAPIViewMixin, RetrieveAPIView):
    """Returns details of a slide."""

    serializer_class = SlideSerializer
    queryset = Slide.visible_objects.order_by("order")


class FrontpageArticleListView(AnnouncementsAPIViewMixin, ListAPIView):
    """Returns an overview of all frontpage articles that are currently active."""

    serializer_class = FrontpageArticleSerializer
    queryset = FrontpageArticle.visible_objects.all()


class FrontpageArticleDetailView(AnnouncementsAPIViewMixin, RetrieveAPIView):
    """Returns details of a frontpage article."""

    serializer_class = FrontpageArticleSerializer
    queryset = FrontpageArticle.visible_objects.all()


class AnnouncementListView(AnnouncementsAPIViewMixin, viewsets.ViewSet):
    """Returns a list of announcements."""

    serializer_class = AnnouncementSerializer

    def list(self, request):
        announces = announcements(request)
        serializer = self.serializer_class(
            announces["announcements"] + announces["persistent_announcements"],
            many=True,
        )
        return Response(serializer.data)


class AnnouncementDetailView(AnnouncementsAPIViewMixin, viewsets.ViewSet):
    serializer_class = AnnouncementSerializer

    def hide(self, request, pk):
        close_announcement(request, pk)
        return Response(status=204)
