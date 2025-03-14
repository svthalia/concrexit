from django import forms
from django.apps import apps
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from members.models import Member
from thabloid.models.thabloid_user import ThabloidUser

from .models import Profile


class ProfileForm(forms.ModelForm):
    """Form with all the user editable fields of a Profile model.

    If the profile is minimized, no fields are required, unless the `require_address`
    keyword argument is True, which is set if a user is filling a minimized profile
    in order to be able to create a Renewal.
    """

    birthday = forms.DateField()

    class Meta:
        fields = [
            "birthday",
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
            "receive_registration_confirmation",
            "receive_oldmembers",
            "email_gsuite_only",
        ]
        model = Profile

    def __init__(self, *args, require_address=False, **kwargs):
        super().__init__(*args, **kwargs)
        user = Member.objects.get(pk=kwargs["instance"].user_id)
        for field in [
            "birthday",
            "address_street",
            "address_city",
            "address_postal_code",
            "address_city",
            "address_country",
        ]:
            if require_address or not user.profile.is_minimized:
                self.fields[field].required = True
            else:
                self.fields[field].required = False

        if not kwargs["instance"].user.is_staff:
            self.fields["email_gsuite_only"].widget = self.fields[
                "email_gsuite_only"
            ].hidden_widget()

        if not user.has_been_member() and not kwargs["instance"].receive_oldmembers:
            self.fields["receive_oldmembers"].disabled = True
            self.fields["receive_oldmembers"].help_text = (
                "If you are a past member, receive emails about Thalia events aimed at alumni. "
                "You cannot enable this option, as we don't have any records of you having been a member "
                "(a long time ago, we didn't keep track of this yet). Contact "
                "<a href='mailto:info@thalia.nu'>info@thalia.nu</a> if you want to receive alumni emails."
            )

        self.fields["birthday"].widget.input_type = "date"
        if not user.profile.is_minimized:
            self.fields["birthday"].disabled = True

        self.render_app_specific_profile_form_fields()

    def render_app_specific_profile_form_fields(self):
        """Render app-specific profile form fields."""
        for app in apps.get_app_configs():
            if hasattr(app, "user_profile_form_fields"):
                fields, _ = app.user_profile_form_fields(self.instance)
                self.fields.update(fields)

    def save(self, commit=True):
        instance = super().save(commit)
        if commit:
            if self.cleaned_data["receive_thabloid"]:
                ThabloidUser.objects.get(pk=instance.user.pk).allow_thabloid()
            else:
                ThabloidUser.objects.get(pk=instance.user.pk).disallow_thabloid()

        # Save app-specific fields by calling the callback that was registered
        for app in apps.get_app_configs():
            if hasattr(app, "user_profile_form_fields"):
                _, callback = app.user_profile_form_fields()
                callback(self, instance, commit)

        return instance

    def clean(self):
        if self.cleaned_data.get("phone_number") is not None:
            self.cleaned_data["phone_number"] = self.cleaned_data[
                "phone_number"
            ].replace(" ", "")

        if self.cleaned_data.get("emergency_contact_phone_number") is not None:
            self.cleaned_data["emergency_contact_phone_number"] = self.cleaned_data[
                "emergency_contact_phone_number"
            ].replace(" ", "")
        super().clean()


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
