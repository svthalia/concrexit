"""
Activemembers URL Configuration
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'committees/$', views.committee_index, name='committees'),
    url(r'^committees/(?P<id>\d)/$', views.committee_detail, name='committee'),
    url(r'^boards/$', views.board_index, name='boards'),
    url(r'^boards/(?P<id>\d+)?$', views.board_detail, name='board'),
]
