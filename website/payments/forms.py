from django import forms

from payments.models import BankAccount, Payment
from payments.widgets import SignatureWidget
from django.utils.translation import gettext as _


class BankAccountForm(forms.ModelForm):
    """
    Custom admin form for BankAccount model
    to add the widget for the signature
    """

    direct_debit = forms.BooleanField(
        required=False, label=_("I want to use this account for direct debits")
    )

    class Meta:
        fields = (
            "initials",
            "last_name",
            "iban",
            "bic",
            "signature",
            "valid_from",
            "mandate_no",
            "owner",
        )
        model = BankAccount


class BankAccountAdminForm(forms.ModelForm):
    """
    Custom admin form for BankAccount model
    to add the widget for the signature
    """

    class Meta:
        fields = "__all__"
        model = BankAccount
        widgets = {
            "signature": SignatureWidget(),
        }


class BatchPaymentInlineAdminForm(forms.ModelForm):
    """
    Custom admin form for Payments model
    for the Batch inlines to add remove
    from batch option
    """

    remove_batch = forms.BooleanField(
        required=False, label=_("Remove payment from batch")
    )

    class Meta:
        fields = (
            "amount",
            "processing_date",
            "paid_by",
        )
        model = Payment
