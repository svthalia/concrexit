from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from partners.api.calendarjs.serializers import PartnerEventCalendarJSSerializer
from partners.models import PartnerEvent
from utils.snippets import extract_date_range


class CalendarJSPartnerEventListView(ListAPIView):
    """
    Defines a custom route that outputs the correctly formatted
    events information for CalendarJS, published events only
    """

    serializer_class = PartnerEventCalendarJSSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = None

    def get_queryset(self):
        start, end = extract_date_range(self.request)
        return PartnerEvent.objects.filter(
            end__gte=start, start__lte=end, published=True
        )
