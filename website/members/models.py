import operator
from datetime import date, timedelta
from functools import reduce

from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from localflavor.generic.countries.sepa import IBAN_SEPA_COUNTRIES
from localflavor.generic.models import IBANField

from activemembers.models import Committee
from utils.snippets import datetime_to_lectureyear
from utils.validators import validate_file_extension


class ActiveMemberManager(models.Manager):
    """Get all active members"""
    def get_queryset(self):
        return (super().get_queryset()
                .exclude(user__membership=None)
                .filter(Q(user__membership__until__isnull=True) |
                        Q(user__membership__until__gt=timezone.now().date()))
                .distinct())

    def with_birthdays_in_range(self, from_date, to_date):
        queryset = self.get_queryset().filter(birthday__lte=to_date)

        if (to_date - from_date).days >= 366:
            # 366 is important to also account for leap years
            # Everyone that's born before to_date has a birthday
            return queryset

        delta = to_date - from_date
        dates = [from_date + timedelta(days=i) for i in range(delta.days + 1)]
        monthdays = [
            {"birthday__month": d.month, "birthday__day": d.day}
            for d in dates
        ]
        # Don't get me started (basically, we are making a giant OR query with
        # all days and months that are in the range)
        query = reduce(operator.or_, [Q(**d) for d in monthdays])
        return queryset.filter(query)


class Member(models.Model):
    """This class describes a member"""

    objects = models.Manager()
    active_members = ActiveMemberManager()

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
        verbose_name=_('Student number'),
        max_length=8,
        validators=[validators.RegexValidator(
            regex=r'(s\d{7}|[ezu]\d{6,7})',
            message=_('Enter a valid student- or e/z/u-number.'))],
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
    def earliest_membership(self):
        if not self.membership_set.exists():
            return None
        return self.membership_set.earliest('since')

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
                if x.current_membership and
                x.current_membership.type == membership_type]

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
            'Show your birthday to other members on your profile page and '
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
        null=True,
    )

    initials = models.CharField(
        max_length=20,
        verbose_name=_('Initials'),
        blank=True,
        null=True,
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
                 ('firstname', _('Show only first name')),
                 ('initials', _('Show initials and last name')),
                 ('fullnick', _("Show name like \"John 'nickname' Doe\"")),
                 ('nicklast', _("Show nickname and last name"))),
        default='full',
    )

    photo = models.ImageField(
        verbose_name=_('Photo'),
        upload_to='public/avatars/',
        null=True,
        blank=True,
    )

    event_permissions = models.CharField(
        max_length=9,
        verbose_name=_('Which events can this member attend'),
        choices=(('all', _('All events')),
                 ('no_events', _('User may not attend events')),
                 ('no_drinks', _('User may not attend drinks')),
                 ('nothing', _('User may not attend anything'))),
        default='all',
    )

    @property
    def can_attend_events(self):
        return (self.event_permissions == 'all' or
                self.event_permissions == 'no_drinks')

    # --- Communication preference ----

    language = models.CharField(
        verbose_name=_('Preferred language'),
        help_text=_('Preferred language for e.g. newsletters'),
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

    receive_newsletter = models.BooleanField(
        verbose_name=_('Receive newsletter'),
        help_text=_("Receive the Thalia Newsletter"),
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

    class Meta:
        ordering = ('user__first_name', 'user__last_name')

    def display_name(self):
        pref = self.display_name_preference
        if pref == 'nickname' and self.nickname is not None:
            return self.nickname
        if pref == 'firstname':
            return self.user.first_name
        elif pref == 'initials':
            if self.initials:
                return '{} {}'.format(self.initials, self.user.last_name)
            return self.user.last_name
        elif pref == 'fullnick' and self.nickname is not None:
            return "{} '{}' {}".format(self.user.first_name,
                                       self.nickname,
                                       self.user.last_name)
        elif pref == 'nicklast':
            return "'{}' {}".format(self.nickname,
                                    self.user.last_name)
        else:
            return self.get_full_name() or self.user.username
    display_name.short_description = _('Display name')

    def short_display_name(self):
        pref = self.display_name_preference
        if (self.nickname is not None and
                (pref == 'nickname' or pref == 'nicklast')):
            return self.nickname
        elif pref == 'initials':
            if self.initials:
                return '{} {}'.format(self.initials, self.user.last_name)
            return self.user.last_name
        else:
            return self.user.first_name
        return

    def get_full_name(self):
        return self.user.get_full_name()

    def get_committees(self):
        return Committee.unfiltered_objects.filter(
            Q(committeemembership__member=self) &
            (
                Q(committeemembership__until=None) |
                Q(committeemembership__until__gt=timezone.now())
            )).exclude(active=False)

    def get_absolute_url(self):
        return reverse('members:profile', args=[str(self.user.pk)])

    def clean(self):
        super().clean()
        errors = {}
        if self.display_name_preference in ('nickname', 'fullnick',
                                            'nicklast'):
            if not self.nickname:
                errors.update(
                    {'nickname': _('You need to enter a nickname to use it as '
                                   'display name')})
        raise ValidationError(errors)

    def __str__(self):
        return '{} ({})'.format(self.get_full_name(), self.user.username)


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
        return not self.until or self.until > timezone.now().date()


class BecomeAMemberDocument(models.Model):
    name = models.CharField(max_length=200)
    file = models.FileField(
        upload_to='members/',
        validators=[validate_file_extension],
    )

    def __str__(self):
        return self.name


def gen_stats_member_type(member_types):
    total = dict()
    for member_type in member_types:
        total[member_type] = (Member
                              .active_members
                              .filter(user__membership__type=member_type)
                              .distinct()
                              .count())
    return total


def gen_stats_year(member_types):
    """
    Generate list with 6 entries, where each entry represents the total amount
    of Thalia members in a year. The sixth element contains all the multi-year
    students.
    """
    stats_year = []
    current_year = datetime_to_lectureyear(date.today())

    for i in range(5):
        new = dict()
        for member_type in member_types:
            new[member_type] = (Member
                                .active_members
                                .filter(starting_year=current_year - i)
                                .filter(user__membership__type=member_type)
                                .distinct()
                                .count())
        stats_year.append(new)

    # Add multi year members
    new = dict()
    for member_type in member_types:
        new[member_type] = (Member
                            .active_members
                            .filter(starting_year__lt=current_year - 4)
                            .filter(user__membership__type=member_type)
                            .distinct()
                            .count())
    stats_year.append(new)

    return stats_year
