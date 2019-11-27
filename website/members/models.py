"""Models defined in the members package"""
import logging
import operator
import os
import uuid
from datetime import timedelta
from functools import reduce

from PIL import Image
from django.conf import settings
from django.contrib.auth.models import User, UserManager
from django.core import validators
from django.core.exceptions import ValidationError
from django.core.files.storage import DefaultStorage
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import pgettext_lazy, gettext_lazy as _

from payments.models import BankAccount
from thaliawebsite.settings import THALIA_PAY_ENABLED_PAYMENT_METHOD
from activemembers.models import MemberGroup, MemberGroupMembership
from utils import countries

logger = logging.getLogger(__name__)


class MemberManager(UserManager):
    """Get all members, i.e. all users with a profile."""

    def get_queryset(self):
        return super().get_queryset().exclude(profile=None)


class ActiveMemberManager(MemberManager):
    """Get all active members, i.e. who have a committee membership"""

    def get_queryset(self):
        """Select all committee members"""
        active_memberships = (MemberGroupMembership
                              .active_objects
                              .filter(group__board=None)
                              .filter(group__society=None))

        return (super().get_queryset()
                .filter(membergroupmembership__in=active_memberships)
                .distinct())


class CurrentMemberManager(MemberManager):
    """Get all members with an active membership"""

    def get_queryset(self):
        """
        Select all members who have a current membership
        """
        return (super().get_queryset()
                .exclude(membership=None)
                .filter(Q(membership__until__isnull=True) |
                        Q(membership__until__gt=timezone.now().date()))
                .distinct())

    def with_birthdays_in_range(self, from_date, to_date):
        """
        Select all who are currently a Thalia member and have a
        birthday within the specified range

        :param from_date: the start of the range (inclusive)
        :param to_date: the end of the range (inclusive)
        :paramtype from_date: datetime
        :paramtype to_date: datetime

        :return: the filtered queryset
        :rtype: Queryset
        """
        queryset = (self.get_queryset()
                    .filter(profile__birthday__lte=to_date))

        if (to_date - from_date).days >= 366:
            # 366 is important to also account for leap years
            # Everyone that's born before to_date has a birthday
            return queryset

        delta = to_date - from_date
        dates = [from_date + timedelta(days=i) for i in range(delta.days + 1)]
        monthdays = [
            {"profile__birthday__month": d.month,
             "profile__birthday__day": d.day}
            for d in dates
        ]
        # Don't get me started (basically, we are making a giant OR query with
        # all days and months that are in the range)
        query = reduce(operator.or_, [Q(**d) for d in monthdays])
        return queryset.filter(query)


class Member(User):
    class Meta:
        proxy = True
        ordering = ('first_name', 'last_name')
        permissions = (
            ('nextcloud_admin', _("Access NextCloud as admin")),
        )

    objects = MemberManager()
    current_members = CurrentMemberManager()
    active_members = ActiveMemberManager()

    def __str__(self):
        return '{} ({})'.format(self.get_full_name(), self.username)

    @property
    def current_membership(self):
        """
        The currently active membership of the user. None if not active.

        :return: the currently active membership or None
        :rtype: Membership or None
        """
        membership = self.latest_membership
        if membership and not membership.is_active():
            return None
        return membership

    @property
    def latest_membership(self):
        """Get the most recent membership of this user"""
        if not self.membership_set.exists():
            return None
        return self.membership_set.latest('since')

    @property
    def earliest_membership(self):
        """Get the earliest membership of this user"""
        if not self.membership_set.exists():
            return None
        return self.membership_set.earliest('since')

    def has_been_member(self):
        """Has this user ever been a member?"""
        return self.membership_set.filter(type='member').count() > 0

    def has_been_honorary_member(self):
        """Has this user ever been an honorary member?"""
        return self.membership_set.filter(type='honorary').count() > 0

    def has_active_membership(self):
        """Is this member currently active

        Tested by checking if the expiration date has passed.
        """
        return self.current_membership is not None

    # Special properties for admin site
    has_active_membership.boolean = True
    has_active_membership.short_description = \
        _('Is this user currently active')

    @classmethod
    def all_with_membership(cls, membership_type):
        """
        Get all users who have a specific membership.

        :param membership_type: The membership to select by
        :return: List of users
        :rtype: [Member]
        """
        return [x for x in cls.objects.all()
                if x.current_membership and
                x.current_membership.type == membership_type]

    @property
    def can_attend_events(self):
        """May this user attend events"""
        if not self.profile:
            return False

        return ((self.profile.event_permissions == 'all' or
                 self.profile.event_permissions == 'no_drinks') and
                self.current_membership is not None)

    def get_member_groups(self):
        """Get the groups this user is a member of"""
        return MemberGroup.objects.filter(
            Q(membergroupmembership__member=self) &
            (
                Q(membergroupmembership__until=None) |
                Q(membergroupmembership__until__gt=timezone.now())
            )).exclude(active=False)

    def get_absolute_url(self):
        return reverse('members:profile', args=[str(self.pk)])

    @property
    def tpay_enabled(self):
        """Does this user have a bank account with Direct Debit enabled"""
        bank_accounts = BankAccount.objects.filter(owner=self)
        if THALIA_PAY_ENABLED_PAYMENT_METHOD and bank_accounts.exists():
            if bank_accounts.last().valid:
                return True
        else:
            return False


def _profile_image_path(_instance, _filename):
    """
    Sets the upload path for profile images.

    Makes sure that it's hard to enumerate profile images.

    Also makes sure any user-picked filenames don't survive

    >>> _profile_image_path(None, "bla.jpg")
    public/avatars/...
    >>> "swearword" in _profile_image_path(None, "swearword.jpg")
    False
    """
    return f'public/avatars/{get_random_string(length=16)}'


class Profile(models.Model):
    """This class holds extra information about a member"""

    # No longer yearly membership as a type, use expiration date instead.
    PROGRAMME_CHOICES = (
        ('computingscience', _('Computing Science')),
        ('informationscience', _('Information Sciences')))

    # Preferably this would have been a foreign key to Member instead,
    # but the UserAdmin requires that this is a foreign key to User.
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
        unique=True,
    )

    starting_year = models.IntegerField(
        verbose_name=_('Starting year'),
        help_text=_('The year this member started studying.'),
        blank=True,
        null=True,
    )

    # ---- Address information -----

    address_street = models.CharField(
        max_length=100,
        validators=[validators.RegexValidator(
            regex=r'^.+ \d+.*',
            message=_('please use the format <street> <number>'),
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

    address_country = models.CharField(
        max_length=2,
        choices=countries.EUROPE,
        verbose_name=_('Country'),
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
        max_length=4096,
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
        upload_to=_profile_image_path,
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
                    " partners."),
        default=True,
    )

    receive_newsletter = models.BooleanField(
        verbose_name=_('Receive newsletter'),
        help_text=_("Receive the Thalia Newsletter"),
        default=True,
    )

    # --- Membership preference ----

    auto_renew = models.BooleanField(
        choices=((True, _('Yes, enable auto renewal.')),
                 (False, _('No, manual renewal required.'))),
        verbose_name=_('Automatically renew membership'),
        default=False,
    )

    # --- Active Member preference ---
    email_gsuite_only = models.BooleanField(
        verbose_name=_('Only receive Thalia emails on G Suite-account'),
        help_text=_('If you enable this option you will no longer receive '
                    'emails send to you by Thalia on your personal email '
                    'address. We will only use your G Suite email address.'),
        default=False,
    )

    def display_name(self):
        pref = self.display_name_preference
        if pref == 'nickname' and self.nickname is not None:
            return f"'{self.nickname}'"
        elif pref == 'firstname':
            return self.user.first_name
        elif pref == 'initials':
            if self.initials:
                return '{} {}'.format(self.initials, self.user.last_name)
            return self.user.last_name
        elif pref == 'fullnick' and self.nickname is not None:
            return "{} '{}' {}".format(self.user.first_name,
                                       self.nickname,
                                       self.user.last_name)
        elif pref == 'nicklast' and self.nickname is not None:
            return "'{}' {}".format(self.nickname,
                                    self.user.last_name)
        else:
            return self.user.get_full_name() or self.user.username

    display_name.short_description = _('Display name')

    def short_display_name(self):
        pref = self.display_name_preference
        if (self.nickname is not None and
                (pref == 'nickname' or pref == 'nicklast')):
            return f"'{self.nickname}'"
        elif pref == 'initials':
            if self.initials:
                return '{} {}'.format(self.initials, self.user.last_name)
            return self.user.last_name
        else:
            return self.user.first_name

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.photo:
            self._orig_image = self.photo.name
        else:
            self._orig_image = ""

    def clean(self):
        super().clean()
        errors = {}

        if self.display_name_preference in ('nickname', 'fullnick',
                                            'nicklast'):
            if not self.nickname:
                errors.update(
                    {'nickname': _('You need to enter a nickname to use it as '
                                   'display name')})

        if self.birthday and self.birthday > timezone.now().date():
            errors.update(
                {'birthday': _('A birthday cannot be in the future.')})

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        storage = DefaultStorage()

        if self._orig_image and not self.photo:
            storage.delete(self._orig_image)
            self._orig_image = None

        elif self.photo and self._orig_image != self.photo.name:
            original_image_name = self.photo.name
            logger.debug("Converting image %s", original_image_name)

            with self.photo.open() as image_handle:
                image = Image.open(image_handle)
                image.load()

            # Image.thumbnail does not upscale an image that is smaller
            image.thumbnail(settings.PHOTO_UPLOAD_SIZE, Image.ANTIALIAS)

            # Create new filename to store compressed image
            image_name, _ext = os.path.splitext(original_image_name)
            image_name = storage.get_available_name(f"{image_name}.jpg")
            with storage.open(image_name, 'wb') as new_image_file:
                image.convert("RGB").save(new_image_file, "JPEG")
            self.photo.name = image_name
            super().save(*args, **kwargs)

            # delete original upload.
            storage.delete(original_image_name)

            if self._orig_image:
                logger.info("deleting", self._orig_image)
                storage.delete(self._orig_image)
            self._orig_image = self.photo.name
        else:
            logging.info("We already had this image, skipping thumbnailing")

    def __str__(self):
        return _("Profile for {}").format(self.user)


class Membership(models.Model):
    MEMBER = 'member'
    BENEFACTOR = 'benefactor'
    HONORARY = 'honorary'

    MEMBERSHIP_TYPES = (
        (MEMBER, _('Member')),
        (BENEFACTOR, _('Benefactor')),
        (HONORARY, _('Honorary Member')))

    type = models.CharField(
        max_length=40,
        choices=MEMBERSHIP_TYPES,
        verbose_name=_('Membership type'),
    )

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

    def __str__(self):
        s = _("Membership of type {} for {} ({}) starting {}").format(
            self.get_type_display(), self.user.get_full_name(),
            self.user.username, self.since,
        )
        if self.until is not None:
            s += pgettext_lazy("Membership until x", " until {}").format(
                self.until)
        return s

    def clean(self):
        super().clean()

        errors = {}
        if self.until and (not self.since or self.until < self.since):
            raise ValidationError(
                {'until': _("End date can't be before start date")})

        if self.since is not None:
            memberships = self.user.membership_set.all()
            for membership in memberships:
                if membership.pk == self.pk:
                    continue
                if ((membership.until is None and (
                    self.until is None or self.until > membership.since)) or
                    (self.until is None and self.since < membership.until) or
                    (self.until and membership.until and
                     self.since < membership.until and
                     self.until > membership.since)):
                    errors.update({
                        'since': _('A membership already '
                                   'exists for that period'),
                        'until': _('A membership already '
                                   'exists for that period')})

        if errors:
            raise ValidationError(errors)

    def is_active(self):
        return not self.until or self.until > timezone.now().date()


class EmailChange(models.Model):
    created_at = models.DateTimeField(_('created at'), default=timezone.now)

    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        verbose_name=_('member'),
    )

    email = models.EmailField(_('email'), max_length=254)

    verify_key = models.UUIDField(unique=True, default=uuid.uuid4,
                                  editable=False)
    confirm_key = models.UUIDField(unique=True, default=uuid.uuid4,
                                   editable=False)

    verified = models.BooleanField(
        _('verified'), default=False,
        help_text=_('the new email address is valid')
    )
    confirmed = models.BooleanField(
        _('confirmed'), default=False,
        help_text=_('the old email address was checked')
    )

    def __str__(self):
        return _(
            "Email change request for {} to {} "
            "created at {} "
            "(confirmed: {}, verified: {})."
        ).format(
            self.member, self.email, self.created_at, self.confirmed,
            self.verified
        )

    @property
    def completed(self):
        return self.verified and self.confirmed

    def clean(self):
        super().clean()

        if any(domain in self.email
               for domain in settings.EMAIL_DOMAIN_BLACKLIST):
            raise ValidationError(
                {'email': _('You cannot use an email address '
                            'from this domain for your account.')})

        if self.email == self.member.email:
            raise ValidationError(
                {'email': _("Please enter a new email address.")})
