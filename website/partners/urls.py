from django.conf.urls import url

from . import views

app_name = "partners"

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^partners/(?P<slug>[-\w]+)$', views.partner, name='partner'),
    url(r'^vacancies$', views.vacancies, name='vacancies'),
]
