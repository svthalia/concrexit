from django.conf.urls import url

from . import views

app_name = "announcements"

urlpatterns = [
    url(r'^close-announcement$', views.close_announcement, name='close-announcement')
]
