"""Views provided by the registrations package."""
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.utils import model_ngettext
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect, get_object_or_404
from django.template.defaultfilters import floatformat
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import FormView, CreateView
from django.views.generic.base import TemplateResponseMixin, TemplateView

from members.decorators import membership_required
from members.models import Membership
from . import emails, forms, services
from .models import Entry, Registration, Renewal, Reference


class BecomeAMemberView(TemplateView):
    """View that render a HTML template with context data."""

    template_name = "registrations/become_a_member.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["year_fees"] = floatformat(
            settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_YEAR], 2
        )
        context["study_fees"] = floatformat(
            settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_STUDY], 2
        )
        return context


@method_decorator(staff_member_required, name="dispatch")
@method_decorator(
    permission_required("registrations.review_entries"), name="dispatch",
)
class EntryAdminView(View):
    """View that handles the processing of entries."""

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        entry_qs = Entry.objects.filter(pk=kwargs["pk"])
        try:
            entry = entry_qs.get()
        except Entry.DoesNotExist:
            return redirect("admin:index")

        if action == "accept":
            if not services.check_unique_user(entry):
                messages.error(
                    request,
                    _("Could not accept %s. Username is not unique.")
                    % model_ngettext(entry, 1),
                )
            elif services.accept_entries(request.user.pk, entry_qs) > 0:
                messages.success(
                    request, _("Successfully accepted %s.") % model_ngettext(entry, 1)
                )
            else:
                messages.error(
                    request, _("Could not accept %s.") % model_ngettext(entry, 1)
                )
        elif action == "reject":
            if services.reject_entries(request.user.pk, entry_qs) > 0:
                messages.success(
                    request, _("Successfully rejected %s.") % model_ngettext(entry, 1)
                )
            else:
                messages.error(
                    request, _("Could not reject %s.") % model_ngettext(entry, 1)
                )
        elif action == "resend":
            try:
                emails.send_registration_email_confirmation(entry.registration)
            except Registration.DoesNotExist:
                pass
        elif action == "revert":
            services.revert_entry(request.user.pk, entry)

        if entry_qs.filter(renewal=None).exists():
            content_type = ContentType.objects.get_for_model(Registration)
        else:
            content_type = ContentType.objects.get_for_model(Renewal)

        return redirect(
            f"admin:{content_type.app_label}_{content_type.model}_change", kwargs["pk"],
        )


class ConfirmEmailView(View, TemplateResponseMixin):
    """View that renders an HTML template and confirms the email address of the provided registration."""

    template_name = "registrations/confirm_email.html"

    def get(self, request, *args, **kwargs):
        queryset = Registration.objects.filter(pk=kwargs["pk"])

        processed = 0
        try:
            processed = services.confirm_entry(queryset)
        except ValidationError:
            pass

        if processed == 0:
            return redirect("registrations:register-member")

        registration = queryset.get()

        if (
            registration.membership_type == Membership.BENEFACTOR
            and not registration.no_references
        ):
            emails.send_references_information_message(registration)

        emails.send_new_registration_board_message(registration)

        return self.render_to_response({})


class BaseRegistrationFormView(FormView):
    """View that renders a membership registration form."""

    form_class = forms.MemberRegistrationForm
    template_name = "registrations/register_member.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["google_api_key"] = settings.GOOGLE_PLACES_API_KEY
        context["year_fees"] = floatformat(
            settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_YEAR], 2
        )
        context["study_fees"] = floatformat(
            settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_STUDY], 2
        )
        return context

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("registrations:renew")
        return super().get(request, args, kwargs)

    def form_valid(self, form):
        form.save()
        emails.send_registration_email_confirmation(form.instance)
        return redirect("registrations:register-success")


class MemberRegistrationFormView(BaseRegistrationFormView):
    """View that renders the `member` membership registration form."""

    form_class = forms.MemberRegistrationForm
    template_name = "registrations/register_member.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tpay_enabled"] = (
            settings.THALIA_PAY_ENABLED_PAYMENT_METHOD
            and settings.THALIA_PAY_FOR_NEW_MEMBERS
        )
        return context

    def post(self, request, *args, **kwargs):
        request.POST = request.POST.dict()
        request.POST["language"] = request.LANGUAGE_CODE
        request.POST["membership_type"] = Membership.MEMBER
        return super().post(request, *args, **kwargs)


class BenefactorRegistrationFormView(BaseRegistrationFormView):
    """View that renders the `benefactor` membership registration form."""

    form_class = forms.BenefactorRegistrationForm
    template_name = "registrations/register_benefactor.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tpay_enabled"] = (
            settings.THALIA_PAY_ENABLED_PAYMENT_METHOD
            and settings.THALIA_PAY_FOR_NEW_MEMBERS
        )
        return context

    def post(self, request, *args, **kwargs):
        request.POST = request.POST.dict()
        request.POST["language"] = request.LANGUAGE_CODE
        request.POST["membership_type"] = Membership.BENEFACTOR
        request.POST["length"] = Entry.MEMBERSHIP_YEAR
        request.POST["remarks"] = (
            "Registered as iCIS employee" if "icis_employee" in request.POST else ""
        )
        request.POST["no_references"] = "icis_employee" in request.POST
        return super().post(request, *args, **kwargs)


@method_decorator(login_required, name="dispatch")
class RenewalFormView(FormView):
    """View that renders the membership renewal form."""

    form_class = forms.RenewalForm
    template_name = "registrations/renewal.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["year_fees"] = floatformat(
            settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_YEAR], 2
        )
        context["study_fees"] = floatformat(
            settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_STUDY], 2
        )
        context["latest_membership"] = self.request.member.latest_membership
        context["latest_renewal"] = Renewal.objects.filter(
            Q(member=self.request.member)
            & (
                Q(status=Registration.STATUS_ACCEPTED)
                | Q(status=Registration.STATUS_REVIEW)
            )
        ).last()
        context["was_member"] = Membership.objects.filter(
            user=self.request.member, type=Membership.MEMBER
        ).exists()
        context["benefactor_type"] = Membership.BENEFACTOR
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        member = self.request.member
        if member is not None and member.latest_membership is not None:
            latest_membership = member.latest_membership
            # If latest membership has not ended or does not ends
            # within 1 month: do not show 'year' length
            hide_year_choice = not (
                latest_membership is not None
                and latest_membership.until is not None
                and (latest_membership.until - timezone.now().date()).days <= 31
            )

            if hide_year_choice:
                form.fields["length"].choices = [
                    c
                    for c in form.fields["length"].choices
                    if c[0] != Entry.MEMBERSHIP_YEAR
                ]

        return form

    def post(self, request, *args, **kwargs):
        request.POST = request.POST.dict()
        if request.member.latest_membership.type == Membership.BENEFACTOR:
            request.POST["membership_type"] = Membership.BENEFACTOR
            request.POST["length"] = Entry.MEMBERSHIP_YEAR
        request.POST["member"] = request.member.pk
        request.POST["remarks"] = ""
        request.POST["no_references"] = True

        if request.POST["membership_type"] == Membership.BENEFACTOR:
            request.POST["no_references"] = False
            if Membership.objects.filter(
                user=request.member, type=Membership.MEMBER
            ).exists():
                request.POST["remarks"] = "Was a Thalia member in the past."
                request.POST["no_references"] = True
            if "icis_employee" in request.POST:
                request.POST["remarks"] = "Registered as iCIS employee."
                request.POST["no_references"] = True

        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        renewal = form.save()
        if not renewal.no_references:
            emails.send_references_information_message(renewal)
        emails.send_new_renewal_board_message(renewal)
        return redirect("registrations:renew-success")


@method_decorator(login_required, name="dispatch")
@method_decorator(membership_required, name="dispatch")
class ReferenceCreateView(CreateView):
    """View that renders a reference creation form."""

    model = Reference
    form_class = forms.ReferenceForm
    template_name = "registrations/reference.html"
    entry = None
    success = False

    def get_success_url(self):
        return reverse("registrations:reference-success", args=(self.entry.pk,))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["success"] = self.success
        try:
            context["name"] = self.entry.registration.get_full_name()
        except Registration.DoesNotExist:
            context["name"] = self.entry.renewal.member.get_full_name()

        return context

    def dispatch(self, request, *args, **kwargs):
        self.entry = get_object_or_404(Entry, pk=kwargs.get("pk"))

        if (
            self.entry.no_references
            or self.entry.membership_type != Membership.BENEFACTOR
        ):
            raise Http404

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        request.POST = request.POST.dict()
        request.POST["member"] = request.member.pk
        request.POST["entry"] = kwargs["pk"]
        return super().post(request, *args, **kwargs)
