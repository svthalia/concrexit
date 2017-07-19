from django.conf.urls import include, url

from . import views

app_name = "members"

urlpatterns = [
    url('^become-a-member-document/(?P<pk>[0-9]*)',
        views.get_become_a_member_document,
        name='become-a-member-document'),
    url('^profile/(?P<pk>[0-9]*)$', views.profile, name='profile'),
    url('^profile/edit/$', views.edit_profile, name='edit-profile'),
    url('^members/iban-export/$', views.iban_export, name='iban-export'),
    url('^$', views.index, name='index'),
]
