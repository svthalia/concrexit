"""
Committees URL Configuration
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^details/(?P<committee_id>\d)/$', views.details, name='details'),
    url(r'^boards/(board-(?P<year>\d{4}-\d{4}))?$', views.boards, name='board'),
]
