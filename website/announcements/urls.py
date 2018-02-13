"""The routes defined by this package"""
# pylint: disable=invalid-name
from django.conf.urls import url

from announcements import views

#: the name of this app
app_name = "announcements"

#: the actual routes
urlpatterns = [
    url(r'^close-announcement$',
        views.close_announcement,
        name='close-announcement')
]
