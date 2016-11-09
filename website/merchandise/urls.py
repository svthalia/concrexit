from django.conf.urls import url

from . import views

app_name = "merchandise"

urlpatterns = [
    url(r'^$', views.index, name='index'),
]
