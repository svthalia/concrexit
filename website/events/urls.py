"""Routes defined by the events package"""
from django.conf.urls import url

from events import admin_views
from events.feeds import EventFeed
from events.views import EventIndex, EventDetail, EventRegisterView, \
    RegistrationView, EventCancelView

app_name = "events"

urlpatterns = [
    url(r'admin/(?P<event_id>\d+)/$', admin_views.details,
        name='admin-details'),
    url(r'admin/(?P<event_id>\d+)/registration/(?P<action>[-\w]+)/$',
        admin_views.change_registration,
        name='admin-registration'),
    url(r'admin/(?P<event_id>\d+)/registration/$',
        admin_views.change_registration,
        name='admin-registration'),
    url(r'admin/(?P<event_id>\d+)/export/$', admin_views.export,
        name='export'),
    url(r'admin/(?P<event_id>\d+)/export_email/$', admin_views.export_email,
        name='export_email'),
    url(r'admin/(?P<event_id>\d+)/all_present/$', admin_views.all_present,
        name='all_present'),
    url(r'^(?P<pk>\d+)/$', EventDetail.as_view(), name='event'),
    url(r'^(?P<pk>\d+)/registration/register/$', EventRegisterView.as_view(),
        name='register'),
    url(r'^(?P<pk>\d+)/registration/cancel/$', EventCancelView.as_view(),
        name='cancel'),
    url(r'^(?P<pk>\d+)/registration/$', RegistrationView.as_view(),
        name='registration'),
    url(r'^$', EventIndex.as_view(),
        name='index'),
    url(r'^ical/nl.ics', EventFeed(lang='nl'),
        name='ical-nl'),
    url(r'^ical/en.ics', EventFeed(),
        name='ical-en'),
]
