from django.conf.urls import url

from . import views


urlpatterns = [
    url('^(?P<slug>[0-9a-z-_]+)', views.album, name='album'),
    url('^download/(?P<slug>[0-9a-z-_]*)', views.download, name='download'),
    url('^$', views.index, name='index'),
]
