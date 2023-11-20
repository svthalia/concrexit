"""Views provided by the registrations package."""
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.defaultfilters import floatformat
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import CreateView, FormView
from django.views.generic.base import TemplateResponseMixin, TemplateView

from members.decorators import membership_required
from members.models import Membership

from . import emails, forms, services
from .models import Entry, Reference, Registration, Renewal


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
    permission_required("registrations.review_entries"),
    name="dispatch",
)
class EntryAdminView(View):
    """View that handles the processing of entries."""

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        entry = get_object_or_404(Entry, pk=kwargs["pk"])

        registration = getattr(entry, "registration", None)
        renewal = getattr(entry, "renewal", None)

        if action == "accept":
            if registration is not None:
                if not registration.check_user_is_unique():
                    messages.error(
                        request,
                        f"Could not accept {registration}. Username or email is not unique.",
                    )
                else:
                    services.accept_registration(registration, actor=request.user)
                    messages.success(request, f"Successfully accepted {registration}.")
            elif renewal is not None:
                services.accept_renewal(renewal, actor=request.user)
                messages.success(request, f"Successfully accepted {renewal}.")
        elif action == "reject":
            if registration is not None:
                services.reject_registration(registration, actor=request.user)
                messages.success(request, f"Successfully rejected {registration}.")
            elif renewal is not None:
                services.reject_renewal(renewal, actor=request.user)
                messages.success(request, f"Successfully rejected {renewal}.")
        elif action == "resend":
            if registration is not None:
                emails.send_registration_email_confirmation(entry.registration)
                messages.success(
                    request, f"Resent registration email of {registration}."
                )
            else:
                messages.error(request, "Cannot resend renewal.")
        elif action == "revert":
            if registration is not None:
                services.revert_registration(registration, actor=request.user)
                messages.success(
                    request, f"Successfully reverted registration {registration}."
                )
            elif renewal is not None:
                services.revert_renewal(renewal, actor=request.user)
                messages.success(request, f"Successfully reverted renewal {renewal}.")

        redirect_model = "registration" if registration is not None else "renewal"
        return redirect(f"admin:registrations_{redirect_model}_change", kwargs["pk"])


class ConfirmEmailView(View, TemplateResponseMixin):
    """View that confirms the email address of the provided registration."""

    template_name = "registrations/confirm_email.html"

    def get(self, request, *args, **kwargs):
        registration = get_object_or_404(Registration, pk=kwargs["pk"])

        if registration.status == Registration.STATUS_CONFIRM:
            services.confirm_registration(registration)

        if registration.status != Registration.STATUS_REVIEW:
            raise Http404

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

        if (
            self.request.member.latest_membership
            and not self.request.member.latest_membership.is_active()
        ) and self.request.member.profile.is_minimized:
            messages.warning(
                self.request,
                _(
                    "You seem to have been a member in the past, but your profile data has been deleted. Please contact the board to renew your membership."
                ),
            )
        context["benefactor_type"] = Membership.BENEFACTOR
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        member = self.request.member
        if member is not None and member.latest_membership is not None:
            latest_membership = member.latest_membership
            # If latest membership has not ended or does not ends
            # within 1 month: do not show 'year' length and disable benefactor option
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
                form.fields["membership_type"].choices = [
                    c
                    for c in form.fields["membership_type"].choices
                    if c[0] != Membership.BENEFACTOR
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
