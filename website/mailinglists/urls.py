from django.conf.urls import include, url

from . import views

app_name = "mailinglists"

urlpatterns = [
    url('^', views.index, name='index'),
]
