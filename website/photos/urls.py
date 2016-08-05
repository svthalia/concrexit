from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^download/(?P<path>.*)', views.download, name='download'),
    url(r'^(?P<slug>[0-9a-z-_]+)', views.album, name='album'),
    url(r'^$', views.index, name='index'),
]
