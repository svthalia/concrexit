from django.conf.urls import url

from . import views

urlpatterns = [
    url('^(?P<pk>\d+)/$', views.preview, name='preview'),
    url(r'admin/send/(?P<pk>\d+)/$', views.admin_send, name='admin-send'),
]
