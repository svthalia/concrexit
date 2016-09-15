from __future__ import unicode_literals

import unicodedata

from django.forms import ModelForm
from .models import Member
from django.contrib.auth.hashers import (
    UNUSABLE_PASSWORD_PREFIX, identify_hasher,
)
from django.utils.translation import ugettext, ugettext_lazy as _


class MemberForm(ModelForm):
    class Meta:
        fields = ['address_street', 'address_street2',
                  'address_postal_code', 'address_city', 'phone_number',
                  'emergency_contact', 'emergency_contact_phone_number',
                  'birthday', 'show_birthday', 'website',
                  'profile_description', 'nickname',
                  'display_name_preference', 'photo', 'language',
                  'receive_optin', 'receive_newsletter']
        model = Member
