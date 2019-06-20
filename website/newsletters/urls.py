"""The routes defined by the newsletters package"""
from django.conf.urls import url

from . import views

app_name = "newsletters"

urlpatterns = [
    url(r'^(?P<pk>\d+)/$', views.preview, name='preview'),
    url(r'^(?P<pk>\d+)/(?P<lang>[-\w]+)/$', views.preview,
        name='preview-localised'),
    url(r'admin/send/(?P<pk>\d+)/$', views.admin_send, name='admin-send'),
]
