from django.conf.urls import url
from django.urls import path

from . import views

app_name = "members"

urlpatterns = [
    url('^profile/(?P<pk>[0-9]*)$', views.profile, name='profile'),
    url('^profile/edit/$', views.edit_profile, name='edit-profile'),
    url('^members/iban-export/$', views.iban_export, name='iban-export'),
    path('profile/change-email/', views.EmailChangeFormView.as_view(),
         name='email-change'),
    path('profile/change-email/verify/<uuid:key>/',
         views.EmailChangeVerifyView.as_view(), name='email-change-verify'),
    path('profile/change-email/confirm/<uuid:key>/',
         views.EmailChangeConfirmView.as_view(), name='email-change-confirm'),
    url('^$', views.index, name='index'),
]
