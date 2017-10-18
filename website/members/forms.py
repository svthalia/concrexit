from __future__ import unicode_literals

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.template import loader
from django.utils import translation
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _

from .models import Profile


class ProfileForm(forms.ModelForm):
    class Meta:
        fields = ['address_street', 'address_street2',
                  'address_postal_code', 'address_city', 'phone_number',
                  'emergency_contact', 'emergency_contact_phone_number',
                  'show_birthday', 'website',
                  'profile_description', 'nickname',
                  'display_name_preference', 'photo', 'language',
                  'receive_optin', 'receive_newsletter']
        model = Profile

    def clean(self):
        super().clean()
        errors = {}
        direct_debit_authorized = self.cleaned_data\
            .get('direct_debit_authorized')
        bank_account = self.cleaned_data.get('bank_account')
        if direct_debit_authorized and not bank_account:
            errors.update({'bank_account': _('Please enter a bank account')})

        raise forms.ValidationError(errors)


class UserCreationForm(BaseUserCreationForm):
    # Don't forget to edit the formset in admin.py!
    # This is a stupid quirk of the user admin.

    # shadow the password fields to prevent validation errors,
    #   since we generate the passwords dynamically.
    password1 = None
    password2 = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ('email', 'first_name', 'last_name'):
            self.fields[field].required = True

    send_welcome_email = forms.BooleanField(
        label=_('Send welcome email'),
        help_text=_('This email will include the generated password'),
        required=False,
        initial=True)

    def clean(self):
        if 'username' in self.cleaned_data:
            self.cleaned_data['username'] = (self.cleaned_data['username']
                                             .lower())
        super().clean()

    def save(self, commit=True):
        password = User.objects.make_random_password(length=15)
        # pass the password on as if it was filled in, so that save() works
        self.cleaned_data['password1'] = password
        user = super().save(commit=False)
        user.set_password(password)
        if commit:
            user.save()
        if self.cleaned_data['send_welcome_email']:
            # Ugly way to get the language since member isn't available
            language = str(self.data.get('profile-0-language', 'en'))
            if language not in ('nl', 'en'):
                language = 'en'
            with translation.override(language):
                email_body = loader.render_to_string(
                    'members/email/welcome.txt',
                    {
                     'full_name': user.get_full_name(),
                     'username': user.username,
                     'password': password
                     })
                user.email_user(
                    ugettext('Welcome to Study Association Thalia'),
                    email_body)
        return user

    class Meta:
        fields = ('username',
                  'first_name',
                  'last_name',
                  'send_welcome_email')


class UserChangeForm(BaseUserChangeForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        if 'username' in self.cleaned_data:
            self.cleaned_data['username'] = (self.cleaned_data['username']
                                             .lower())
        super().clean()
