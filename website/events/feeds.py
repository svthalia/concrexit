"""The feeds defined by the events package."""
from django.conf import settings
from django.db.models.query_utils import Q
from django.urls import reverse
from django.utils.translation import activate
from django.utils.translation import gettext as _

from django_ical.views import ICalFeed

from events.models import Event, FeedToken


class EventFeed(ICalFeed):
    """Output an iCal feed containing all published events."""

    def __init__(self, lang="en"):
        super().__init__()
        self.lang = lang
        self.user = None

    def __call__(self, request, *args, **kwargs):
        if "u" in request.GET:
            self.user = FeedToken.get_member(request.GET["u"])
        else:
            self.user = None

        return super().__call__(request, args, kwargs)

    def product_id(self):
        return f"-//{settings.SITE_DOMAIN}//EventCalendar//{self.lang.upper()}"

    def file_name(self):
        return f"thalia_{self.lang}.ics"

    def title(self):
        activate(self.lang)
        return _("Study Association Thalia event calendar")

    def items(self):
        query = Q(published=True)

        if self.user:
            query &= Q(eventregistration__member=self.user) & Q(
                eventregistration__date_cancelled=None
            )

        return Event.objects.filter(query).order_by("-start")

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return f'{item.description} <a href="' f'{self.item_link(item)}">Website</a>'

    def item_start_datetime(self, item):
        return item.start

    def item_end_datetime(self, item):
        return item.end

    def item_link(self, item):
        return settings.BASE_URL + reverse("events:event", kwargs={"pk": item.id})

    def item_location(self, item):
        return f"{item.location} - {item.map_location}"
