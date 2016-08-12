from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^download/(?P<path>.*)', views.download, name='download'),
    url(r'^shared-download/(?P<slug>[-\w]+)/(?P<token>[a-zA-Z0-9]+)/(?P<path>.*)', views.shared_download, name='shared-download'),
    url(r'^shared-thumbnail/(?P<slug>[-\w]+)/(?P<token>[a-zA-Z0-9]+)/(?P<size_fit>\d+x\d+_[01])/(?P<path>.*)', views.shared_thumbnail, name='shared-thumbnail'),
    url(r'^(?P<slug>[-\w]+)/$', views.album, name='album'),
    url(r'^(?P<slug>[-\w]+)/(?P<token>[a-zA-Z0-9]+)$', views.shared_album, name='shared_album'),
    url(r'^$', views.index, name='index'),
]
