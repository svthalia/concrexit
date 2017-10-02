from django.conf.urls import url

from . import views

app_name = "pushnotifications"

urlpatterns = [
    url(r'admin/send/(?P<pk>\d+)/$', views.admin_send, name='admin-send'),
]
