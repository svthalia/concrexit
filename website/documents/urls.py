from django.conf.urls import include, url

from . import views

app_name = "documents"
urlpatterns = [
    url('^miscellaneous/(?P<pk>[0-9]*)', views.get_miscellaneous_document,
        name='miscellaneous-document'),
    url('^(?P<document_type>(policy-document|annual-report|financial-report))/'
        '(?P<year>[0-9]{4})',
        views.get_association_document,
        name='association-document'),
    url('^general-meeting/(?P<pk>[0-9]*)/', include([
        url('^minutes', views.get_general_meeting_minutes,
            name='minutes'),
        # TODO can we make this URL more pretty, using e.g. document seq nrs?
        url('^(?P<document_pk>[0-9]*)', views.get_general_meeting_document,
            name='general-meeting-document'),
    ])),
    url('^', views.index, name='index'),
]
