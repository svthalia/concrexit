from django.conf.urls import url

from . import views

app_name = "thabloid"

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^viewer/(?P<year>[0-9]{4})/(?P<issue>[0-9]+)/$', views.viewer, name='viewer'),
]
