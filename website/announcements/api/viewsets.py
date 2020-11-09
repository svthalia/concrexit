from rest_framework import viewsets

from announcements.api.serializers import SlideSerializer
from announcements.models import Slide


class SlideViewset(viewsets.ReadOnlyModelViewSet):
    """
    Viewset for slides
    """

    queryset = Slide.objects.all()
    serializer_class = SlideSerializer

    def get_queryset(self):
        queryset = Slide.objects.all()
        if not self.request.member:
            queryset = queryset.filter(members_only=False)

        ids = (
            slide.pk
            for slide in queryset
            if slide.event_set.exists() or slide.is_visible
        )

        return Slide.objects.filter(pk__in=ids)
