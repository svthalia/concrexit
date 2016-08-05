"""
Events URL Configuration
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'admin/(?P<event_id>\d+)/$', views.admin_details, name='admin-details'),
]
