from django.conf.urls import url
from django.views.generic.base import RedirectView

from . import views

app_name = "education"

urlpatterns = [
    url('^exam/(?P<id>[0-9]*)/$', views.exam, name="exam"),
    url('^summary/(?P<id>[0-9]*)/$', views.summary, name="summary"),
    url('^exam/submit/$', views.submit_exam, name="submit-exam"),
    url('^summary/submit/$', views.submit_summary, name="submit-summary"),
    url('^exam/submit/(?P<id>[0-9]*)/$', views.submit_exam, name="submit-exam"),
    url('^summary/submit/(?P<id>[0-9]*)/$', views.submit_summary, name="submit-summary"),
    url('^courses/$', views.courses, name="courses"),
    url('^courses/(?P<id>[0-9]*)/$', views.course, name="course"),
    url('^books/$', views.books, name="books"),
    url('^$',
        RedirectView.as_view(pattern_name='education:courses',
                             permanent=True), name="index"),
]
