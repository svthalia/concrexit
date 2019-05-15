from django import forms

from payments.models import BankAccount
from payments.widgets import SignatureWidget
from django.utils.translation import gettext as _


class BankAccountForm(forms.ModelForm):
    """
    Custom admin form for BankAccount model
    to add the widget for the signature
    """

    direct_debit = forms.BooleanField(
        required=False,
        label=_('I want to use this account for direct debits')
    )

    class Meta:
        fields = ('initials', 'last_name', 'iban', 'bic',
                  'signature', 'valid_from', 'mandate_no', 'owner')
        model = BankAccount


class BankAccountAdminForm(forms.ModelForm):
    """
    Custom admin form for BankAccount model
    to add the widget for the signature
    """

    class Meta:
        fields = '__all__'
        model = BankAccount
        widgets = {
            'signature': SignatureWidget(),
        }
