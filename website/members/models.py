from django.utils import timezone
from django.db import models
from django.core import validators
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from localflavor.generic.countries.sepa import IBAN_SEPA_COUNTRIES
from localflavor.generic.models import IBANField

from utils.validators import validate_file_extension


class Member(models.Model):
    """This class describes a member"""

    # No longer yearly membership as a type, use expiration date instead.
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

    starting_year = models.IntegerField(
        verbose_name=_('Starting year'),
        help_text=_('The year this member started studying.'),
        blank=True,
        null=True,
    )

    @property
    def current_membership(self):
        membership = self.latest_membership
        if membership and not membership.is_active():
            return None
        return membership

    @property
    def latest_membership(self):
        if not self.membership_set.exists():
            return None
        return self.membership_set.latest('since')

    @property
    def membership_set(self):
        return self.user.membership_set

    def is_active(self):
        """Is this member currently active

        Tested by checking if the expiration date has passed.
        """
        return self.current_membership is not None
    # Special properties for admin site
    is_active.boolean = True
    is_active.short_description = _('Is this user currently active')

    @classmethod
    def all_with_membership(cls, membership_type, prefetch=None):
        return [x for x in cls.objects.all().prefetch_related(prefetch)
                if x.current_membership
                and x.current_membership.type == membership_type]

    # ---- Address information -----

    address_street = models.CharField(
        max_length=100,
        validators=[validators.RegexValidator(
            regex=r'^.+ \d+.*',
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
        max_length=20,
        verbose_name=_('Phone number'),
        help_text=_('Enter a phone number so Thalia may reach you'),
        validators=[validators.RegexValidator(
            regex=r'^\+?\d+$',
            message=_('Please enter a valid phone number'),
        )],
        null=True,
        blank=True,
    )

    # ---- Emergency contact ----

    emergency_contact = models.CharField(
        max_length=255,
        verbose_name=_('Emergency contact name'),
        help_text=_('Who should we contact in case of emergencies'),
        null=True,
        blank=True,
    )

    emergency_contact_phone_number = models.CharField(
        max_length=20,
        verbose_name=_('Emergency contact phone number'),
        help_text=_('The phone number for the emergency contact'),
        validators=[validators.RegexValidator(
            regex=r'^\+?\d+$',
            message=_('Please enter a valid phone number'),
        )],
        null=True,
        blank=True,
    )

    # ---- Personal information ------

    birthday = models.DateField(
        verbose_name=_('Birthday'),
        null=True
    )

    show_birthday = models.BooleanField(
        verbose_name=_('Display birthday'),
        help_text=_(
            'Show the birthday on your profile page and '
            'in the birthday calendar'),
        default=True,
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
        blank=True,
    )

    nickname = models.CharField(
        max_length=30,
        verbose_name=_('Nickname'),
        blank=True,
        null=True,
    )

    display_name_preference = models.CharField(
        max_length=10,
        verbose_name=_('How to display name'),
        choices=(('full', _('Show full name')),
                 ('nickname', _('Show only nickname')),
                 ('initials', _('Show initials and last name')),
                 ('fullnick', _("Show name like \"John 'nickname' Doe\"")),
                 ('nicklast', _("Show nickname and last name"))),
        default='full',
    )

    photo = models.ImageField(
        verbose_name=_('Foto'),
        upload_to='public/avatars/',
        null=True,
        blank=True,
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
        help_text=_('Bank account for direct debit'),
        include_countries=IBAN_SEPA_COUNTRIES,
        blank=True,
    )

    def display_name(self):
        pref = self.display_name_preference
        if pref == 'nickname':
            return self.nickname
        elif pref == 'initials':
            return '{} {}'.format(self.initials, self.user.last_name)
        elif pref == 'fullnick':
            return "{} '{}' {}".format(self.user.first_name,
                                       self.nickname,
                                       self.user.last_name)
        elif pref == 'nicklast':
            return "'{}' {}".format(self.nickname,
                                    self.user.last_name)
        else:
            return self.user.get_full_name()
    display_name.short_description = _('Display name')

    def __str__(self):
        return self.display_name()


class Membership(models.Model):

    MEMBERSHIP_TYPES = (
        ('member', _('Member')),
        ('supporter', _('Supporter')),
        ('honorary', _('Honorary Member')))

    type = models.CharField(
        max_length=40,
        choices=MEMBERSHIP_TYPES,
        verbose_name=_('Membership type'),
    )

    # Preferably this would have been a foreign key to Member instead,
    # but Django currently does not support nested inlines in the Admin UI.
    # This is necessary to create an inline in the User form.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('User'),
    )

    since = models.DateField(
        verbose_name=_("Membership since"),
        help_text=_("The date the member started holding this membership."),
        default=timezone.now
    )

    until = models.DateField(
        verbose_name=_("Membership until"),
        help_text=_("The date the member stops holding this membership."),
        blank=True,
        null=True,
    )

    @property
    def member(self):
        return self.user.member

    def is_active(self):
        return not self.until or self.until > timezone.now()


class BecomeAMemberDocument(models.Model):
    name = models.CharField(max_length=200)
    file = models.FileField(
        upload_to='members/',
        validators=[validate_file_extension],
    )

    def __str__(self):
        return self.name
