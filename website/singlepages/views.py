"""Views of the singlepages app."""
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView


@method_decorator(login_required, "dispatch")
class StyleGuideView(TemplateView):
    """Static page with the style guide."""

    template_name = "singlepages/styleguide.html"


@method_decorator(login_required, "dispatch")
class BecomeActiveView(TemplateView):
    """Static page with info about becoming an active member."""

    template_name = "singlepages/become_active.html"


class PrivacyPolicyView(TemplateView):
    """Static page with the privacy policy."""

    template_name = "singlepages/privacy_policy.html"


class ResponsibleDisclosureView(TemplateView):
    """Static page with the responsible disclosure policy."""

    template_name = "singlepages/responsible_disclosure.html"


class EventTermsView(TemplateView):
    """Static page with the event registration terms."""

    template_name = "singlepages/event_registration_terms.html"


class SiblingAssociationsView(TemplateView):
    """Static page with the sibling associations."""

    template_name = "singlepages/sibling_associations.html"


class ContactView(TemplateView):
    """Static page with contact info."""

    template_name = "singlepages/contact.html"


class StudentWellBeingView(TemplateView):
    """Static page with info on student well-being."""

    template_name = "singlepages/student_well-being.html"
