from django.conf.urls import url

from . import views

app_name = "thaliapp"
urlpatterns = [
    url(r'^login', views.login,
        name='thaliapp-login'),
    url(r'^app', views.app,
        name='thaliapp-app'),
]
