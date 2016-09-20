"""
Events URL Configuration
"""

from django.conf.urls import url

from events.feeds import EventFeed
from . import views

urlpatterns = [
    url(r'admin/(?P<event_id>\d+)/$', views.admin_details, name='admin-details'),
    url(r'admin/(?P<event_id>\d+)/export/$', views.export, name='export'),
    url(r'^(?P<event_id>\d+)$', views.event, name='event'),
    url(r'^$', views.index, name='index'),
    url(r'^ical/nl.ics', EventFeed(lang='nl'), name='ical-nl'),
    url(r'^ical/en.ics', EventFeed(), name='ical-en'),
]
