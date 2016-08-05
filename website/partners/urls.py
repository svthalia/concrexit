from django.conf.urls import url

from . import views

app_name = "partners"
urlpatterns = [
    url('^', views.index, name='index'),
]
