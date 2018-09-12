"""The routes defined by the activemembers package"""
from django.conf.urls import url

from . import views


app_name = "activemembers"

urlpatterns = [
    url(r'committees/$', views.committee_index, name='committees'),
    url(r'^committees/(?P<pk>\d+)/$', views.committee_detail, name='committee'),
    url(r'societies/$', views.society_index, name='societies'),
    url(r'^societies/(?P<pk>\d+)/$', views.society_detail, name='society'),
    url(r'^boards/$', views.board_index, name='boards'),
    url(r'^board/(?P<since>\d{4})$', views.board_detail, name='board'),
    url(r'^board/(?P<since>\d{4})-(?P<until>\d{4})$', views.board_detail, name='board'),
]
