from django.conf.urls import include, url

from . import views

app_name = "documents"

urlpatterns = [
    url(r'^miscellaneous/(?P<pk>[0-9]+)/$', views.get_miscellaneous_document,
        name='miscellaneous-document'),
    url(r'^(?P<document_type>(policy-document|annual-report|financial-report))/'
        r'(?P<year>[0-9]{4})/$',
        views.get_association_document,
        name='association-document'),
    url(r'^general-meeting/(?P<pk>[0-9]+)/', include([
        url(r'^minutes/$', views.get_general_meeting_minutes,
            name='minutes'),
        # TODO can we make this URL more pretty, using e.g. document seq nrs?
        url(r'^(?P<document_pk>[0-9]+)/$', views.get_general_meeting_document,
            name='general-meeting-document'),
    ])),
    url(r'^$', views.index, name='index'),
]
