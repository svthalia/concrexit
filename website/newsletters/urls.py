from django.conf.urls import url

from . import views

app_name = "newsletters"

urlpatterns = [
    url('^(?P<pk>\d+)/$', views.preview, name='preview'),
    url('^(?P<pk>\d+)/(?P<lang>[-\w]+)/$', views.preview,
        name='preview-localised'),
    url(r'admin/send/(?P<pk>\d+)/$', views.admin_send, name='admin-send'),
    url('^(?P<year>\d+)/(?P<week>\d+)/nieuwsbrief.html',
        views.legacy_redirect, name='legacy-redirect')
]
