"""The feeds defined by the events package"""
from django.db.models.query_utils import Q
from django.contrib.sites.models import Site
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.utils.translation import activate
from django_ical.views import ICalFeed

from events.models import Event, FeedToken


class EventFeed(ICalFeed):
    """Output an iCal feed containing all published events"""
    def __init__(self, lang='en'):
        super().__init__()
        self.lang = lang
        self.user = None

    def __call__(self, request, *args, **kwargs):
        if 'u' in request.GET:
            self.user = FeedToken.get_member(request.GET['u'])
        else:
            self.user = None

        return super().__call__(request, args, kwargs)

    def product_id(self):
        return '-//thalia.nu//EventCalendar//' + self.lang.upper()

    def file_name(self):
        return "thalia_{}.ics".format(self.lang)

    def title(self):
        activate(self.lang)
        return _('Study Association Thalia event calendar')

    def items(self):
        query = Q(published=True)

        if self.user:
            query &= (Q(registration_start__isnull=True) |
                      Q(registration__member=self.user))

        return Event.objects.filter(query).order_by('-start')

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return (item.description +
                ' <a href="https://%s%s">Website</a>' %
                (Site.objects.get_current().domain,
                 self.item_link(item)))

    def item_start_datetime(self, item):
        return item.start

    def item_end_datetime(self, item):
        return item.end

    def item_link(self, item):
        return reverse('events:event', kwargs={'pk': item.id})

    def item_location(self, item):
        return "{} - {}".format(item.location, item.map_location)
