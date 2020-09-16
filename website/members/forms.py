"""Forms defined by the members package"""
from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from members import emails
from .models import Profile


class ProfileForm(forms.ModelForm):
    """Form with all the user editable fields of a Profile model"""

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
    """
    Custom Form that removes the password fields from user creation
    and sends a welcome message when a user is created
    """

    # Don't forget to edit the formset in admin.py!
    # This is a stupid quirk of the user admin.

    # shadow the password fields to prevent validation errors,
    #   since we generate the passwords dynamically.
    password1 = None
    password2 = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ("email", "first_name", "last_name"):
            self.fields[field].required = True

    send_welcome_email = forms.BooleanField(
        label=_("Send welcome email"),
        help_text=_("This email will include the generated password"),
        required=False,
        initial=True,
    )

    def clean(self):
        if "username" in self.cleaned_data:
            self.cleaned_data["username"] = self.cleaned_data["username"].lower()
        super().clean()

    def save(self, commit=True):
        password = User.objects.make_random_password(length=15)
        # pass the password on as if it was filled in, so that save() works
        self.cleaned_data["password1"] = password
        user = super().save(commit=False)
        user.set_password(password)
        if commit:
            user.save()
        if self.cleaned_data["send_welcome_email"]:
            language = settings.LANGUAGE_CODE
            emails.send_welcome_message(user, password, language)
        return user

    class Meta:
        fields = ("username", "first_name", "last_name", "send_welcome_email")


class UserChangeForm(BaseUserChangeForm):
    """
    Custom user edit form that adds fields for first/last name and email
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        if "username" in self.cleaned_data:
            self.cleaned_data["username"] = self.cleaned_data["username"].lower()
        super().clean()
