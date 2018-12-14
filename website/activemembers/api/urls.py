from django.urls import path

from activemembers.api import views

urlpatterns = [
    path('activemembers/nextcloud/users', views.NextCloudUsersView.as_view()),
    path('activemembers/nextcloud/groups', views.NextCloudGroupsView.as_view()),
]
