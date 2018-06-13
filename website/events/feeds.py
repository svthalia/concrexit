"""The feeds defined by the events package"""
from django.contrib.sites.models import Site
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.utils.translation import activate
from django_ical.views import ICalFeed

from events.models import Event


class EventFeed(ICalFeed):
    """Output an iCal feed containing all published events"""
    def __init__(self, lang='en'):
        super().__init__()
        self.lang = lang

    def product_id(self):
        return '-//thalia.nu//EventCalendar//' + self.lang.upper()

    def file_name(self):
        return "thalia_{}.ics".format(self.lang)

    def title(self):
        activate(self.lang)
        return _('Study Association Thalia event calendar')

    def items(self):
        return Event.objects.filter(published=True).order_by('-start')

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
