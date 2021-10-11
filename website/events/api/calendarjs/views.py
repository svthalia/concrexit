from django.db.models import Q, Count, OuterRef, Subquery

from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticatedOrReadOnly

from events.api.calendarjs.serializers import (
    EventsCalenderJSSerializer,
    UnpublishedEventsCalenderJSSerializer,
)
from events.api.calendarjs.permissions import UnpublishedEventPermissions
from events.models import Event, EventRegistration
from utils.snippets import extract_date_range


class CalendarJSEventListView(ListAPIView):
    """Define a custom route that outputs the correctly formatted events information for CalendarJS, published events only."""

    serializer_class = EventsCalenderJSSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = None

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["member"] = self.request.member
        return context

    def get_queryset(self):
        start, end = extract_date_range(self.request)
        objects = Event.objects.filter(end__gte=start, start__lte=end, published=True)\
            .annotate(user_reg=Subquery(EventRegistration.objects
                                        .filter(event=OuterRef('id'), member=self.request.member)
                                        .values('member')))
            # .annotate(user_reg=Count('eventregistration', filter=Q(member=self.request.member)))
        return objects


class CalendarJSUnpublishedEventListView(ListAPIView):
    """Define a custom route that outputs the correctly formatted events information for CalendarJS, unpublished events only."""

    serializer_class = UnpublishedEventsCalenderJSSerializer
    permission_classes = [IsAdminUser, UnpublishedEventPermissions]
    pagination_class = None

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["member"] = self.request.member
        return context

    def get_queryset(self):
        start, end = extract_date_range(self.request)
        return Event.objects.filter(end__gte=start, start__lte=end, published=False)
