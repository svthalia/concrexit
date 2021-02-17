"""Forms defined by the members package."""
from django import forms
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from .models import Profile


class ProfileForm(forms.ModelForm):
    """Form with all the user editable fields of a Profile model."""

    class Meta:
        fields = [
            "show_birthday",
            "address_street",
            "address_street2",
            "address_postal_code",
            "address_city",
            "address_country",
            "phone_number",
            "emergency_contact",
            "emergency_contact_phone_number",
            "website",
            "profile_description",
            "nickname",
            "initials",
            "display_name_preference",
            "photo",
            "receive_optin",
            "receive_newsletter",
            "receive_magazine",
            "email_gsuite_only",
        ]
        model = Profile

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not kwargs["instance"].user.is_staff:
            self.fields["email_gsuite_only"].widget = self.fields[
                "email_gsuite_only"
            ].hidden_widget()


class UserCreationForm(BaseUserCreationForm):
    """Custom Form that lowercases the username on creation."""

    def clean(self):
        if "username" in self.cleaned_data:
            self.cleaned_data["username"] = self.cleaned_data["username"].lower()
        super().clean()

    class Meta:
        fields = ("username", "first_name", "last_name")


class UserChangeForm(BaseUserChangeForm):
    """Custom user edit form that adds fields for first/last name and email.

    It also force-lowercases the username on save
    """

    username = forms.CharField(
        label=_("Username"),
        required=True,
        help_text=_("Required. 64 characters or fewer. Letters and digits only."),
        widget=forms.TextInput(attrs={"class": "vTextField", "maxlength": 64}),
        validators=[
            RegexValidator(
                regex="^[a-zA-Z0-9]{1,64}$",
                message=_(
                    "Please use 64 characters or fewer. Letters and digits only."
                ),
            )
        ],
    )

    first_name = forms.CharField(
        label=_("First name"),
        required=True,
        widget=forms.TextInput(attrs={"class": "vTextField", "maxlength": 30}),
    )
    last_name = forms.CharField(
        label=_("Last name"),
        required=True,
        widget=forms.TextInput(attrs={"class": "vTextField", "maxlength": 150}),
    )
    email = forms.CharField(
        label=_("Email address"),
        required=True,
        widget=forms.EmailInput(attrs={"class": "vTextField", "maxlength": 254}),
    )

    def clean(self):
        if "username" in self.cleaned_data:
            self.cleaned_data["username"] = self.cleaned_data["username"].lower()
        super().clean()
