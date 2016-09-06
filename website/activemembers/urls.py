"""
Activemembers URL Configuration
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^committees$', views.committees, name='committees'),
    url(r'^committees/(?P<committee_id>\d)/$', views.details, name='details'),
    url(r'^boards/(board-(?P<year>\d{4}-\d{4}))?$', views.boards, name='board'),
]
