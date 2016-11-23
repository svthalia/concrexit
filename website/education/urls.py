from django.conf.urls import include, url
from django.views.generic.base import RedirectView

from . import views

app_name = "education"

urlpatterns = [
    url(r'^books/$', views.books, name="books"),
    url(r'^courses/', include([
        url(r'^$', views.courses, name="courses"),
        url(r'^(?P<id>[0-9]*)/', include([
            url(r'^$', views.course, name="course"),
            url(r'^upload-exam/$', views.submit_exam, name="submit-exam"),
            url(r'^upload-summary/$', views.submit_summary, name="submit-summary"),
        ])),
    ])),
    url(r'^exams/(?P<id>[0-9]*)/$', views.exam, name="exam"),
    url(r'^summaries/(?P<id>[0-9]*)/$', views.summary, name="summary"),
    url(r'^upload-exam/$', views.submit_exam, name="submit-exam"),
    url(r'^upload-summary/$', views.submit_summary, name="submit-summary"),
    url('^student-participation/$', views.student_participation, name="student-participation"),
    url(r'^$',
        RedirectView.as_view(pattern_name='education:courses',
                             permanent=True), name="index"),
]
