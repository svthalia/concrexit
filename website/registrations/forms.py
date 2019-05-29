"""The forms defined by the registrations package"""
from django import forms
from django.forms import TypedChoiceField
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _

from utils.snippets import datetime_to_lectureyear
from .models import Registration, Renewal


class BaseRegistrationForm(forms.ModelForm):
    """Base form for membership registrations"""

    birthday = forms.DateField(
        widget=forms.widgets.SelectDateWidget(years=[
            year for year in range(timezone.now().year - 50,
                                   timezone.now().year - 10)]),
        label=capfirst(_('birthday'))
    )

    privacy_policy = forms.BooleanField(
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['privacy_policy'].label = mark_safe(_(
            'I accept the <a href="{}">privacy policy</a>.').format(
            reverse_lazy('privacy-policy')))


class MemberRegistrationForm(BaseRegistrationForm):
    """Form for member registrations"""

    this_year = datetime_to_lectureyear(timezone.now())
    years = reversed([(x, "{} - {}".format(x, x + 1)) for x in
                      range(this_year - 20, this_year + 2)])

    starting_year = TypedChoiceField(
        choices=years,
        coerce=int,
        empty_value=this_year,
        required=False
    )

    class Meta:
        model = Registration
        fields = '__all__'
        exclude = ['created_at', 'updated_at', 'status', 'username',
                   'payment', 'membership']


class BenefactorRegistrationForm(BaseRegistrationForm):
    """Form for benefactor registrations"""

    icis_employee = forms.BooleanField(
        required=False,
        label=_('I am an employee of iCIS')
    )

    class Meta:
        model = Registration
        fields = '__all__'
        exclude = ['created_at', 'updated_at', 'status', 'username',
                   'starting_year', 'programme', 'payment', 'membership']


class RenewalForm(forms.ModelForm):
    """Form for membership renewals"""

    privacy_policy = forms.BooleanField(
        required=True,
    )

    icis_employee = forms.BooleanField(
        required=False,
        label=_('I am an employee of iCIS')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['privacy_policy'].label = mark_safe(_(
            'I accept the <a href="{}">privacy policy</a>.').format(
            reverse_lazy('privacy-policy')))

    class Meta:
        model = Renewal
        fields = '__all__'
        exclude = ['created_at', 'updated_at', 'status',
                   'payment', 'membership']
