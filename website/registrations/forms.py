"""The forms defined by the registrations package"""
from django import forms
from django.forms import TypedChoiceField
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from payments.widgets import PaymentWidget
from utils.snippets import datetime_to_lectureyear
from .models import Registration, Renewal


class MemberRegistrationForm(forms.ModelForm):
    """Form for membership registrations"""
    birthday = forms.DateField(
        widget=forms.widgets.SelectDateWidget(years=[
            year for year in range(timezone.now().year - 50,
                                   timezone.now().year - 10)]),
        label=_('birthday')
    )

    privacy_policy = forms.BooleanField(
        required=True,
        label=_('I accept the privacy policy')
    )

    this_year = datetime_to_lectureyear(timezone.now())
    years = reversed([(x, "{} - {}".format(x, x + 1)) for x in
                      range(this_year - 20, this_year + 2)])

    starting_year = TypedChoiceField(
        choices=years,
        coerce=int,
        empty_value=this_year
    )

    class Meta:
        model = Registration
        fields = '__all__'
        exclude = ['created_at', 'updated_at', 'status', 'username', 'remarks',
                   'payment', 'membership']


class MemberRenewalForm(forms.ModelForm):
    """Form for membership renewals"""

    privacy_policy = forms.BooleanField(
        required=True,
        label=_('I accept the privacy policy')
    )

    class Meta:
        model = Renewal
        fields = '__all__'
        exclude = ['created_at', 'updated_at', 'status', 'remarks']
