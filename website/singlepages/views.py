"""Views of the singlepages app"""
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from thaliawebsite.settings import settings


@method_decorator(login_required, "dispatch")
class StyleGuideView(TemplateView):
    """Static page with the style guide"""

    template_name = "singlepages/styleguide.html"


@method_decorator(login_required, "dispatch")
class BecomeActiveView(TemplateView):
    """Static page with info about becoming an active member"""

    template_name = "singlepages/become_active.html"


class PrivacyPolicyView(TemplateView):
    """Static page with the privacy policy"""

    template_name = "singlepages/privacy_policy.html"


class EventTermsView(TemplateView):
    """Static page with the event registration terms"""

    template_name = "singlepages/event_registration_terms.html"


class SiblingAssociationsView(TemplateView):
    """Static page with the sibling associations"""

    template_name = "singlepages/sibling_associations.html"


class ContactView(TemplateView):
    """Static page with contact info"""

    template_name = "singlepages/contact.html"


@method_decorator(login_required, "dispatch")
class AlmanacView(TemplateView):
    """Static page with url to almanac info"""

    template_name = "singlepages/almanac.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_almanac"] = settings.SHOW_ALMANAC_PAGE
        if settings.SHOW_ALMANAC_PAGE:
            member = self.request.member
            context["member"] = member
            almanac_url = (
                f"https://svthalia.typeform.com/to/Equ1fY?"
                f"thalia_email={member.email}&"
                f"thalia_username={member.get_username()}&"
                f"thalia_full_name={member.get_full_name()}&"
                f"thalia_cohort={member.profile.starting_year}&"
                f"thalia_user_id={member.id}"
            )
            context["almanac_url"] = almanac_url
        return context
