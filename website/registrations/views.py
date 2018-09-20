"""Views provided by the registrations package"""
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.utils import model_ngettext
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.template.defaultfilters import floatformat
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.generic import FormView
from django.views.generic.base import TemplateResponseMixin, TemplateView

from members.models import Membership
from . import emails, forms, services
from .models import Entry, Registration, Renewal


class BecomeAMemberView(TemplateView):
    """View that render a HTML template with context data"""
    template_name = 'registrations/become_a_member.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['year_fees'] = floatformat(settings.MEMBERSHIP_PRICES[
                                               Entry.MEMBERSHIP_YEAR], 2)
        context['study_fees'] = floatformat(settings.MEMBERSHIP_PRICES[
                                                Entry.MEMBERSHIP_STUDY], 2)
        context['member_form_url'] = reverse('registrations:register')
        return context


@method_decorator(staff_member_required, name='dispatch')
@method_decorator(permission_required('registrations.review_entries'),
                  name='dispatch', )
class EntryAdminView(View):
    """
    View that handles the review processing of entries
    """

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        entry_qs = Entry.objects.filter(pk=kwargs['pk'])
        try:
            entry = entry_qs.get()
        except Entry.DoesNotExist:
            return redirect('admin:index')

        if action == 'accept':
            if not services.check_unique_user(entry):
                messages.error(request, _('Could not accept %s. '
                                          'Username is not unique.') %
                               model_ngettext(entry, 1))
            elif services.accept_entries(entry_qs) > 0:
                messages.success(request, _('Successfully accepted %s.') %
                                 model_ngettext(entry, 1))
            else:
                messages.error(request, _('Could not accept %s.') %
                               model_ngettext(entry, 1))
        elif action == 'reject':
            if services.reject_entries(entry_qs) > 0:
                messages.success(request, _('Successfully rejected %s.') %
                                 model_ngettext(entry, 1))
            else:
                messages.error(request, _('Could not reject %s.') %
                               model_ngettext(entry, 1))

        if entry_qs.filter(renewal=None).exists():
            content_type = ContentType.objects.get_for_model(Registration)
        else:
            content_type = ContentType.objects.get_for_model(Renewal)

        return redirect("admin:%s_%s_change" %
                        (content_type.app_label, content_type.model),
                        kwargs['pk'])


class ConfirmEmailView(View, TemplateResponseMixin):
    """
    View that renders an HTML template and confirms the email address
    of the provided registration
    """
    template_name = 'registrations/confirm_email.html'

    def get(self, request, *args, **kwargs):
        entry = Entry.objects.filter(pk=kwargs['pk'])

        processed = 0
        try:
            processed = services.confirm_entry(entry)
        except ValidationError:
            pass

        if processed == 0:
            return redirect('registrations:register')

        emails.send_new_registration_board_message(entry.get())

        return self.render_to_response({})


class MemberRegistrationFormView(FormView):
    """
    View that renders the membership registration form
    """
    form_class = forms.MemberRegistrationForm
    template_name = 'registrations/register_member.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['year_fees'] = floatformat(settings.MEMBERSHIP_PRICES[
                                               Entry.MEMBERSHIP_YEAR], 2)
        context['study_fees'] = floatformat(settings.MEMBERSHIP_PRICES[
                                                Entry.MEMBERSHIP_STUDY], 2)
        context['privacy_policy_url'] = reverse('privacy-policy')
        return context

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('registrations:renew')
        return super().get(request, args, kwargs)

    def post(self, request, *args, **kwargs):
        request.POST = request.POST.dict()
        request.POST['language'] = request.LANGUAGE_CODE
        request.POST['membership_type'] = Membership.MEMBER
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        return redirect('registrations:register-success')


@method_decorator(login_required, name='dispatch')
class RenewalFormView(FormView):
    """
    View that renders the membership renewal form
    """
    form_class = forms.MemberRenewalForm
    template_name = 'registrations/renewal.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['year_fees'] = floatformat(settings.MEMBERSHIP_PRICES[
                                               Entry.MEMBERSHIP_YEAR], 2)
        context['study_fees'] = floatformat(settings.MEMBERSHIP_PRICES[
                                                Entry.MEMBERSHIP_STUDY], 2)
        context['membership'] = self.request.member.latest_membership
        if context['membership'] is not None:
            context['membership_type'] = (context['membership']
                                          .get_type_display())
        context['privacy_policy_url'] = reverse('privacy-policy')
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        member = self.request.member
        if member is not None and member.latest_membership is not None:
            latest_membership = member.latest_membership
            # If latest membership has not ended or does not ends
            # within 1 month: do not show 'year' length
            hide_year_choice = not (latest_membership is not None and
                                    latest_membership.until is not None and
                                    (latest_membership.until -
                                     timezone.now().date()).days <= 31)

            if hide_year_choice:
                form.fields['length'].choices = [
                    c for c in form.fields['length'].choices
                    if c[0] != Entry.MEMBERSHIP_YEAR
                ]

        return form

    def post(self, request, *args, **kwargs):
        request.POST = request.POST.dict()
        request.POST['member'] = request.member.pk
        request.POST['membership_type'] = Membership.MEMBER
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        renewal = form.save()
        emails.send_new_renewal_board_message(renewal)
        return redirect('registrations:renew-success')
