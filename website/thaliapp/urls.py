from django.conf.urls import url
from rest_framework.authtoken import views as rfviews

from . import views

app_name = "thaliapp"
urlpatterns = [
    url(r'^login', views.login,
        name='thaliapp-login'),
    url(r'^app', views.app,
        name='thaliapp-app'),
    url(r'^randomasaservice', views.raas,
        name='thaliapp-raas'),
]
