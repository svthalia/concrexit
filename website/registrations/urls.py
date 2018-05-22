"""The routes defined by the registrations package"""
from django.urls import path
from django.views.generic import TemplateView

from .views import (BecomeAMemberView, ConfirmEmailView,
                    EntryAdminView, MemberRegistrationFormView,
                    RenewalFormView)

app_name = "registrations"

urlpatterns = [
    path('', BecomeAMemberView.as_view(), name='index'),
    path('register/', MemberRegistrationFormView.as_view(), name='register'),
    path('register/success/', TemplateView.as_view(
        template_name='registrations/register_success.html'),
        name='register-success'),
    path('renew/', RenewalFormView.as_view(), name='renew'),
    path('renew/success/', TemplateView.as_view(
         template_name='registrations/renewal_success.html'),
         name='renew-success'),
    path('admin/accept/<uuid:pk>/',
         EntryAdminView.as_view(action='accept'),
         name='admin-accept'),
    path('admin/reject/<uuid:pk>/',
         EntryAdminView.as_view(action='reject'),
         name='admin-reject'),
    path('confirm-email/<uuid:pk>/',
         ConfirmEmailView.as_view(), name='confirm-email'),
]
