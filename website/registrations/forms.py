"""The forms defined by the registrations package."""
from django import forms
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.forms import TypedChoiceField
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from members.models import Membership
from payments.widgets import SignatureWidget
from registrations import services
from .models import Registration, Renewal, Reference


class BaseRegistrationForm(forms.ModelForm):
    """Base form for membership registrations."""

    birthday = forms.DateField(
        widget=forms.widgets.SelectDateWidget(
            years=range(timezone.now().year - 50, timezone.now().year - 10)
        ),
        label=capfirst(_("birthday")),
    )

    privacy_policy = forms.BooleanField(required=True,)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["privacy_policy"].label = mark_safe(
            _('I accept the <a href="{}">privacy policy</a>.').format(
                reverse_lazy("singlepages:privacy-policy")
            )
        )


class RegistrationAdminForm(forms.ModelForm):
    """Custom admin form for Registration model to add the widget for the signature."""

    class Meta:
        fields = "__all__"
        model = Registration
        widgets = {
            "signature": SignatureWidget(),
        }


class MemberRegistrationForm(BaseRegistrationForm):
    """Form for member registrations."""

    this_year = timezone.now().year
    years = reversed(
        [(x, "{} - {}".format(x, x + 1)) for x in range(this_year - 20, this_year + 1)]
    )

    starting_year = TypedChoiceField(
        choices=years,
        coerce=int,
        empty_value=this_year,
        required=False,
        help_text=_("What lecture year did you start studying at Radboud University?"),
    )

    class Meta:
        model = Registration
        widgets = {
            "signature": SignatureWidget(),
        }
        fields = (
            "length",
            "first_name",
            "last_name",
            "birthday",
            "email",
            "phone_number",
            "student_number",
            "programme",
            "starting_year",
            "address_street",
            "address_street2",
            "address_postal_code",
            "address_city",
            "address_country",
            "optin_birthday",
            "optin_mailinglist",
            "membership_type",
            "direct_debit",
            "initials",
            "iban",
            "bic",
            "signature",
        )


class BenefactorRegistrationForm(BaseRegistrationForm):
    """Form for benefactor registrations."""

    icis_employee = forms.BooleanField(
        required=False, label=_("I am an employee of iCIS")
    )

    class Meta:
        model = Registration
        widgets = {
            "signature": SignatureWidget(),
        }
        fields = (
            "length",
            "first_name",
            "last_name",
            "birthday",
            "email",
            "phone_number",
            "student_number",
            "address_street",
            "address_street2",
            "address_postal_code",
            "address_city",
            "address_country",
            "optin_birthday",
            "optin_mailinglist",
            "contribution",
            "membership_type",
            "direct_debit",
            "initials",
            "iban",
            "bic",
            "signature",
        )


class RenewalForm(forms.ModelForm):
    """Form for membership renewals."""

    privacy_policy = forms.BooleanField(required=True,)

    icis_employee = forms.BooleanField(
        required=False, label=_("I am an employee of iCIS")
    )

    contribution = forms.IntegerField(required=False,)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["privacy_policy"].label = mark_safe(
            _('I accept the <a href="{}">privacy policy</a>.').format(
                reverse_lazy("singlepages:privacy-policy")
            )
        )

    class Meta:
        model = Renewal
        fields = ("member", "length", "contribution", "membership_type")


class ReferenceForm(forms.ModelForm):
    def clean(self):
        super().clean()
        membership = self.cleaned_data["member"].current_membership
        if membership and membership.type == Membership.BENEFACTOR:
            raise ValidationError(_("Benefactors cannot give references."))

        membership = self.cleaned_data["member"].latest_membership
        if (
            membership
            and membership.until
            and membership.until < services.calculate_membership_since()
        ):
            raise ValidationError(
                _(
                    "It's not possible to give references for "
                    "memberships that start after your own "
                    "membership's end."
                )
            )

    class Meta:
        model = Reference
        fields = "__all__"
        error_messages = {
            NON_FIELD_ERRORS: {
                "unique_together": _(
                    "You've already given a reference for this person."
                ),
            }
        }
