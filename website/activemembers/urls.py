"""
Activemembers URL Configuration
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^committees$', views.committees, name='committees'),
    url(r'^committees/(?P<committee_id>\d)/$', views.details, name='details'),
    url(r'^boards/(?P<id>\d+)?$', views.boards, name='board'),
]
