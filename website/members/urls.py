from django.conf.urls import url

from . import views


urlpatterns = [
    url('^become-a-member-document/(?P<pk>[0-9]*)', views.get_become_a_member_document, name='become-a-member-document'),
    url('^', views.index),
]
