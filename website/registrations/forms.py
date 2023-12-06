from django import forms
from django.conf import settings
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.forms import HiddenInput, TypedChoiceField
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from members.models import Membership
from payments.widgets import SignatureWidget
from registrations import services

from .models import Reference, Registration, Renewal


class BaseRegistrationForm(forms.ModelForm):
    """Base form for membership registrations.

    Subclasses must implement setting the right contribution.
    """

    birthday = forms.DateField(
        label=capfirst(_("birthday")),
    )

    privacy_policy = forms.BooleanField(
        required=True,
    )

    direct_debit = forms.BooleanField(
        required=False,
        label=_("Pay via direct debit"),
        help_text=_(
            "This will allow you to sign a Direct Debit mandate, allowing Thalia to withdraw the membership fees from your bank account. Also, you will be able to use this bank account for future payments to Thalia via Thalia Pay."
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["privacy_policy"].label = mark_safe(
            _('I accept the <a href="{}">privacy policy</a>.').format(
                reverse_lazy("singlepages:privacy-policy")
            )
        )
        self.fields["birthday"].widget.input_type = "date"

    def clean(self):
        if self.cleaned_data.get("phone_number") is not None:  # pragma: no cover
            self.cleaned_data["phone_number"] = self.cleaned_data[
                "phone_number"
            ].replace(" ", "")
        super().clean()


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
        [(x, f"{x} - {x + 1}") for x in range(this_year - 20, this_year + 1)]
    )

    starting_year = TypedChoiceField(
        choices=years,
        coerce=int,
        empty_value=this_year,
        required=False,
        help_text=_("What lecture year did you start studying at Radboud University?"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student_number"].required = True
        self.fields["programme"].required = True
        self.fields["starting_year"].required = True

    class Meta:
        model = Registration
        widgets = {
            "signature": SignatureWidget(),
            # Contribution needs to be a field to be able to set it from .clean().
            "contribution": HiddenInput(),
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
            "contribution",
            "membership_type",
            "direct_debit",
            "initials",
            "iban",
            "bic",
            "signature",
        )

    def clean(self):
        super().clean()
        self.cleaned_data["contribution"] = settings.MEMBERSHIP_PRICES[
            self.cleaned_data["length"]
        ]

        return self.cleaned_data


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

    privacy_policy = forms.BooleanField(
        required=True,
    )

    icis_employee = forms.BooleanField(
        required=False, label=_("I am an employee of iCIS")
    )

    contribution = forms.DecimalField(
        required=False,
        max_digits=5,
        decimal_places=2,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["privacy_policy"].label = mark_safe(
            _('I accept the <a href="{}">privacy policy</a>.').format(
                reverse_lazy("singlepages:privacy-policy")
            )
        )
        self.fields["length"].help_text = (
            "A discount of €7,50 will be applied if you upgrade your (active) year membership "
            "to a membership until graduation. You will only have to pay €22,50 in that case."
        )

    class Meta:
        model = Renewal
        fields = (
            "member",
            "length",
            "contribution",
            "membership_type",
            "no_references",
            "remarks",
        )

    def clean(self):
        super().clean()

        if self.cleaned_data["length"] == Renewal.MEMBERSHIP_STUDY:
            now = timezone.now()
            if Membership.objects.filter(
                user=self.cleaned_data["member"],
                type=Membership.MEMBER,
                until__gte=now,
                since__lte=now,
            ).exists():
                # The membership upgrade discount applies if, at the time a Renewal is
                # created, the user has an active 'member' type membership for a year.
                self.cleaned_data["contribution"] = (
                    settings.MEMBERSHIP_PRICES[Renewal.MEMBERSHIP_STUDY]
                    - settings.MEMBERSHIP_PRICES[Renewal.MEMBERSHIP_YEAR]
                )
            else:
                self.cleaned_data["contribution"] = settings.MEMBERSHIP_PRICES[
                    Renewal.MEMBERSHIP_STUDY
                ]
        elif self.cleaned_data["membership_type"] == Membership.MEMBER:
            self.cleaned_data["contribution"] = settings.MEMBERSHIP_PRICES[
                self.cleaned_data["length"]
            ]

        return self.cleaned_data


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
                "It's not possible to give references for memberships "
                "that start after your own membership's end."
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
