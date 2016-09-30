from __future__ import unicode_literals

from django import forms
from django.contrib.auth.models import User
from django.template import loader
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from .models import Member


class MemberForm(forms.ModelForm):
    class Meta:
        fields = ['address_street', 'address_street2',
                  'address_postal_code', 'address_city', 'phone_number',
                  'emergency_contact', 'emergency_contact_phone_number',
                  'show_birthday', 'website',
                  'profile_description', 'nickname',
                  'display_name_preference', 'photo', 'language',
                  'receive_optin', 'receive_newsletter']
        model = Member


class UserCreationForm(forms.ModelForm):
    # Don't forget to edit the formset in admin.py!
    # This is a stupid quirk of the user admin.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ('email', 'first_name', 'last_name'):
            self.fields[field].required = True

    send_welcome_email = forms.BooleanField(
        label=_('Send welcome email'),
        help_text=_('This email will include the generated password'),
        initial=True)

    def save(self, commit=True):
        password = User.objects.make_random_password(length=15)
        user = super().save(commit=False)
        user.set_password(password)
        if commit:
            user.save()
        if self.cleaned_data['send_welcome_email']:
            with translation.override(user.member.language):
                email_body = loader.render_to_string(
                    'members/email/welcome.txt',
                    {'user': user, 'password': password})
            user.email_user(
                _('Welkom bij Studievereniging Thalia'),
                email_body)
        return user

    class Meta:
        fields = ('username',
                  'first_name',
                  'last_name',
                  'send_welcome_email')
