from django.conf.urls import include, url

from . import views

app_name = "documents"

urlpatterns = [
    url(r'^document/(?P<pk>[0-9]+)/$', views.get_document, name='document'),
    url(r'^$', views.index, name='index'),
]
