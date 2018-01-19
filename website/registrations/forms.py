from django import forms
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from .models import Registration, Renewal


class MemberRegistrationForm(forms.ModelForm):
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

    class Meta:
        model = Registration
        fields = '__all__'
        exclude = ['created_at', 'updated_at', 'status', 'username', 'remarks']


class MemberRenewalForm(forms.ModelForm):
    class Meta:
        model = Renewal
        fields = '__all__'
        exclude = ['created_at', 'updated_at', 'status', 'remarks']
