"""API v2 views of the announcements app."""

from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
)

from announcements.api.v2.serializers import SlideSerializer, FrontpageArticleSerializer
from announcements.models import Slide, FrontpageArticle


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
