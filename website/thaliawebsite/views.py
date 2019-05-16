"""General views for the website"""

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import (HttpResponseForbidden, HttpResponse)
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.views.generic.base import View


class IndexView(TemplateView):
    template_name = 'index.html'


@method_decorator(login_required, 'dispatch')
class StyleGuideView(TemplateView):
    """Static page with the style guide"""
    template_name = 'singlepages/styleguide.html'


@method_decorator(login_required, 'dispatch')
class BecomeActiveView(TemplateView):
    """Static page with info about becoming an active member"""
    template_name = 'singlepages/become_active.html'


class PrivacyPolicyView(TemplateView):
    """Static page with the privacy policy"""
    template_name = 'singlepages/privacy_policy.html'


class EventTermsView(TemplateView):
    """Static page with the event registration terms"""
    template_name = 'singlepages/event_registration_terms.html'


class SiblingAssociationsView(TemplateView):
    """Static page with the sibling associations"""
    template_name = 'singlepages/sibling_associations.html'


class ContactView(TemplateView):
    """Static page with contact info"""
    template_name = 'singlepages/contact.html'


@method_decorator(staff_member_required, 'dispatch')
class TestCrashView(View):
    """Test view to intentionally crash to test the error handling."""
    def dispatch(self, request, *args, **kwargs) -> HttpResponse:
        if not request.user.is_superuser:
            return HttpResponseForbidden("This is not for you")
        raise Exception("Test exception")
