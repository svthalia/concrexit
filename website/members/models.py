from datetime import datetime

from django.db import models
from django.core import validators
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from localflavor.generic.countries.sepa import IBAN_SEPA_COUNTRIES
from localflavor.generic.models import IBANField


class Member(models.Model):
    """This class describes a member"""

    # No longer yearly membership as a type, use expiration date instead.
    MEMBERSHIP_TYPES = (
        ('benefactor', _('Benefactor')),
        ('member', _('Member')),
        ('honorary', _('Honorary Member')))

    PROGRAMME_CHOICES = (
        ('computingscience', _('Computing Science')),
        ('informationscience', _('Information Sciences')))

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    # ----- Registration information -----

    programme = models.CharField(
        max_length=20,
        choices=PROGRAMME_CHOICES,
        verbose_name=_('Study programme'),
        blank=True,
        null=True,
    )

    student_number = models.CharField(
        max_length=8,
        validators=[validators.RegexValidator(
            regex=r'(s\d{7}|[ezu]\d{6,7})',
            message=_('Enter a valid student- of e/z/u-number.'))],
        blank=True,
        null=True,
    )

    membership_type = models.CharField(
        max_length=40,
        choices=MEMBERSHIP_TYPES,
        verbose_name=_('Membership type'),
    )

    registration_year = models.IntegerField(
        verbose_name=_('Registration year'),
        help_text=_('The year this member first became a part of Thalia'),
        default=lambda: datetime.utcnow().year,
    )

    membership_expiration = models.DateField(
        verbose_name=_('Expiration date of membership'),
        help_text=_('Let the membership expire after this time'),
        null=True,
        blank=True,
    )

    # ---- Address information -----

    address_street = models.CharField(
        max_length=100,
        validators=[validators.RegexValidator(
            regex=r'^.+ \d+.+',
            message=_('Include the house number'),
        )],
        verbose_name=_('Street and house number'),
        null=True,
    )

    address_street2 = models.CharField(
        max_length=100,
        verbose_name=_('Second address line'),
        blank=True,
        null=True,
    )

    address_postal_code = models.CharField(
        max_length=10,
        verbose_name=_('Postal code'),
        null=True,
    )

    address_city = models.CharField(
        max_length=40,
        verbose_name=_('City'),
        null=True,
    )

    phone_number = models.CharField(
        max_length=13,
        verbose_name=_('Phone number'),
        help_text=_('Enter a phone number so Thalia may reach you'),
        validators=[validators.RegexValidator(
            regex=r'^\+?\d+$',
            message=_('Voer een geldig telefoonnummer in.'),
        )],
        null=True,
        blank=True,
    )

    # ---- Parents' address ----

    parent_address_street = models.CharField(
        max_length=100,
        validators=[validators.RegexValidator(
            regex=r'^.+ \d+.+',
            message=_('Include the house number'),
        )],
        verbose_name=_('Street and house number'),
        null=True,
    )

    parent_address_street2 = models.CharField(
        max_length=100,
        verbose_name=_('Second address line'),
        blank=True,
        null=True,
    )

    parent_address_postal_code = models.CharField(
        max_length=10,
        verbose_name=_('Postal code'),
        null=True,
    )

    parent_address_city = models.CharField(
        max_length=40,
        verbose_name=_('City'),
        null=True,
    )

    parent_phone_number = models.CharField(
        max_length=13,
        verbose_name=_('Phone number'),
        help_text=_('Enter a phone number so Thalia may reach you'),
        validators=[validators.RegexValidator(
            regex=r'^\+?\d+$',
            message=_('Voer een geldig telefoonnummer in.'),
        )],
        null=True,
        blank=True,
    )

    # ---- Personal information ------

    birthday = models.DateField(
        verbose_name=_('Birthday'),
        null=True
    )

    website = models.URLField(
        max_length=200,
        verbose_name=_('Website'),
        help_text=_('Website to display on your profile page'),
        blank=True,
        null=True
    )

    profile_description = models.TextField(
        verbose_name=_('Profile text'),
        help_text=_('Text to display on your profile'),
    )

    nickname = models.CharField(
        max_length=30,
        verbose_name=_('Nickname'),
        blank=True,
        null=True,
    )

    # --- Communication preference ----

    language = models.CharField(
        verbose_name=_('Preferred language'),
        help_text=_('Preferred language for e.g. news letters'),
        max_length=5,
        choices=settings.LANGUAGES,
        default='nl',
    )

    receive_optin = models.BooleanField(
        verbose_name=_('Receive opt-in mailings'),
        help_text=_("Receive mailings about vacancies and events from Thalia's"
                    " sponsors."),
        default=True,
    )

    # --- Direct debit information ----

    direct_debit_authorized = models.BooleanField(
        choices=((True, _('Yes, I want Thalia to take the membership fees '
                          'from my bank account through direct debit for '
                          'each year.')),
                 (False, _('No, I will pay the contribution myself'))),
        verbose_name=_('Direct debit'),
        help_text=_('Each year, have Thalia take the membership fees from my '
                    'bank account'),
        default=False,
    )

    bank_account = IBANField(
        verbose_name=_('Bank account'),
        include_countries=IBAN_SEPA_COUNTRIES
    )
