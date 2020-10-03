"""Defines the routes provided in this package"""
from django.urls import path, include

from . import views

#: the name of the application
app_name = "merchandise"

#: the urls provided by this package
urlpatterns = [
    path("association/merchandise/", include([path("", views.index, name="index"),]))
]
