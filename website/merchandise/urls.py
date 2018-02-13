"""Defines the routes provided in this package"""
# pylint: disable=invalid-name
from django.conf.urls import url

from . import views

#: the name of the application
app_name = "merchandise"

#: the urls provided by this package
urlpatterns = [
    url(r'^$', views.index, name='index'),
]
