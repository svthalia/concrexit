from django import forms
from django.utils.translation import gettext as _

from payments.models import BankAccount, Payment
from payments.widgets import SignatureWidget


class BankAccountForm(forms.ModelForm):
    """Custom admin form for BankAccount model to add the widget for the signature."""

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


class BankAccountUserRevokeForm(forms.ModelForm):
    """Custom form for members to revoke their bank account."""

    def is_valid(self):
        return super().is_valid() and self.instance.can_be_revoked

    class Meta:
        fields = ("valid_until",)
        model = BankAccount


class BankAccountAdminForm(forms.ModelForm):
    """Custom admin form for BankAccount model to add the widget for the signature."""

    class Meta:
        fields = "__all__"
        model = BankAccount
        widgets = {
            "signature": SignatureWidget(),
        }


class PaymentCreateForm(forms.Form):
    """Custom form to create a payment by a user."""

    app_label = forms.CharField(max_length=255, widget=forms.HiddenInput())
    model_name = forms.CharField(max_length=255, widget=forms.HiddenInput())
    payable = forms.CharField(max_length=255, widget=forms.HiddenInput())
    next = forms.CharField(max_length=255, widget=forms.HiddenInput())
    payable_hash = forms.CharField(max_length=255, widget=forms.HiddenInput())

    class Meta:
        fields = "__all__"


class BatchPaymentInlineAdminForm(forms.ModelForm):
    """Custom admin form for Payments model for the Batch inlines to add remove from batch option."""

    remove_batch = forms.BooleanField(
        required=False, label=_("Remove payment from batch")
    )

    class Meta:
        fields = (
            "topic",
            "paid_by",
            "amount",
            "created_at",
            "notes",
        )
        model = Payment
