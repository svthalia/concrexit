"""Routes defined by the events package"""
from django.conf.urls import url
from django.urls import path

from events import admin_views
from events.feeds import EventFeed
from events.views import EventIndex, EventDetail, EventRegisterView, \
    RegistrationView, EventCancelView

app_name = "events"

urlpatterns = [
    path('<int:pk>/', EventDetail.as_view(), name='event'),
    path('<int:pk>/registration/register/', EventRegisterView.as_view(),
         name='register'),
    path('<int:pk>/registration/cancel/', EventCancelView.as_view(),
         name='cancel'),
    path('<int:pk>/registration/', RegistrationView.as_view(),
         name='registration'),
    path('', EventIndex.as_view(), name='index'),
    path('ical/nl.ics', EventFeed(lang='nl'), name='ical-nl'),
    path('ical/en.ics', EventFeed(), name='ical-en'),
]
