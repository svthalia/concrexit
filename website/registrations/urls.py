from django.conf.urls import url
from django.views.generic import TemplateView

from registrations.views import (BecomeAMemberView, ConfirmEmailView,
                                 EntryAdminView, MemberRegistrationFormView,
                                 PaymentAdminView, RenewalFormView)

app_name = "registrations"

urlpatterns = [
    url(r'^$', BecomeAMemberView.as_view(), name='index'),
    url(r'^register/$', MemberRegistrationFormView.as_view(), name='register'),
    url(r'^register/success/$', TemplateView.as_view(
        template_name='registrations/register_success.html'),
        name='register-success'),
    url(r'^renew/$', RenewalFormView.as_view(),
        name='renew'),
    url(r'^renew/success/$', TemplateView.as_view(
        template_name='registrations/renewal_success.html'),
        name='renew-success'),
    url(r'^admin/accept/(?P<pk>[\w-]+)/$',
        EntryAdminView.as_view(action='accept'),
        name='admin-accept'),
    url(r'^admin/reject/(?P<pk>[\w-]+)/$',
        EntryAdminView.as_view(action='reject'),
        name='admin-reject'),
    url(r'^admin/process/(?P<pk>[\w-]+)/(?P<type>[\w-]+)/$',
        PaymentAdminView.as_view(), name='admin-process'),
    url('^confirm-email/(?P<pk>[\w-]+)/$',
        ConfirmEmailView.as_view(), name='confirm-email'),
]
