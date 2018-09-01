"""The models defined by the activemembers package"""
import datetime
import logging

from django.contrib.auth.models import Permission
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from tinymce import HTMLField

from utils.translation import (ModelTranslateMeta, MultilingualField,
                               localize_attr_name)

logger = logging.getLogger(__name__)


class ActiveMemberGroupsManager(models.Manager):
    """Returns active committees only"""

    def get_queryset(self):
        return (super().get_queryset()
                .exclude(active=False)
                .order_by(localize_attr_name('name')))


class MemberGroup(models.Model, metaclass=ModelTranslateMeta):
    """Describes a committee"""

    objects = models.Manager()
    active_objects = ActiveMemberGroupsManager()

    name = MultilingualField(
        models.CharField,
        max_length=40,
        verbose_name=_('Committee name'),
        unique=True,
    )

    description = MultilingualField(
        HTMLField,
        verbose_name=_('Description'),
    )

    photo = models.ImageField(
        verbose_name=_('Image'),
        upload_to='public/committeephotos/',
        null=True,
        blank=True,
    )

    members = models.ManyToManyField(
        'members.Member',
        through='activemembers.MemberGroupMembership'
    )

    permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('permissions'),
        blank=True,
    )

    since = models.DateField(
        _('founded in'),
        null=True,
        blank=True,
    )

    until = models.DateField(
        _('existed until'),
        null=True,
        blank=True,
    )

    active = models.BooleanField(default=False)

    contact_email = models.EmailField(
        _('contact email address'),
        blank=True,
        null=True,
    )

    contact_mailinglist = models.OneToOneField(
        'mailinglists.MailingList',
        verbose_name=_('contact mailing list'),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    def clean(self):
        if ((self.contact_email is not None and
                self.contact_mailinglist is not None) or
            (self.contact_email is None and
                self.contact_mailinglist is None)):
            raise ValidationError({
                'contact_email':
                    _("Please use either the mailing list "
                      "or email address option."),
                'contact_mailinglist':
                    _("Please use either the mailing list "
                      "or email address option.")
            })

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('activemembers:committee', args=[str(self.pk)])

    class Meta:
        verbose_name = _('member group')
        verbose_name_plural = _('member groups')
        # ordering is done in the manager, to sort on a translated field


class Committee(MemberGroup):
    wiki_namespace = models.CharField(
        _('Wiki namespace'),
        null=True,
        blank=True,
        max_length=50)

    class Meta:
        verbose_name = _('committee')
        verbose_name_plural = _('committees')
        # ordering is done in the manager, to sort on a translated field


class Society(MemberGroup):
    class Meta:
        verbose_name = _('society')
        verbose_name_plural = _('societies')
        # ordering is done in the manager, to sort on a translated field


class Board(MemberGroup):
    class Meta:
        verbose_name = _('board')
        verbose_name_plural = _('boards')
        ordering = ['-since']
        permissions = (
            ('board_wiki', _("Access the board wiki")),
        )

    def save(self, *args, **kwargs):
        self.active = True
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('activemembers:board', args=[str(self.since.year),
                                                    str(self.until.year)])

    def validate_unique(self, *args, **kwargs):
        super().validate_unique(*args, **kwargs)
        boards = Board.objects.all()
        if self.since is not None:
            for board in boards:
                if board.pk == self.pk:
                    continue
                if ((board.until is None and (
                        self.until is None or self.until >= board.since)) or
                        (self.until is None and self.since <= board.until) or
                        (self.until and board.until and
                            self.since <= board.until and
                            self.until >= board.since)):
                    raise ValidationError({
                        'since': _('A board already exists for those years'),
                        'until': _('A board already exists for those years')})


class ActiveMembershipManager(models.Manager):
    """
    Customs manager that gets the currently active committee memberships
    """

    def get_queryset(self):
        return super().get_queryset().exclude(until__lt=timezone.now().date())


class MemberGroupMembership(models.Model, metaclass=ModelTranslateMeta):
    """Describes a group membership"""
    objects = models.Manager()
    active_memberships = ActiveMembershipManager()

    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        verbose_name=_('Member'),
    )

    group = models.ForeignKey(
        MemberGroup,
        on_delete=models.CASCADE,
        verbose_name=_('Committee'),
    )

    since = models.DateField(
        verbose_name=_('Member since'),
        help_text=_('The date this member joined in this role'),
        default=datetime.date.today
    )

    until = models.DateField(
        verbose_name=_('Member until'),
        help_text=_("A member until this time "
                    "(can't be in the future)."),
        blank=True,
        null=True,
    )

    chair = models.BooleanField(
        verbose_name=_('Chair of the committee'),
        help_text=_('There can only be one chair at a time!'),
        default=False,
    )

    role = MultilingualField(
        models.CharField,
        _('role'),
        help_text=_('The role of this member'),
        max_length=255,
        blank=True,
        null=True,
    )

    @property
    def initial_connected_membership(self):
        """Find the oldest membership directly connected to the current one"""
        qs = MemberGroupMembership.objects.filter(
            group=self.group,
            member=self.member,
            until__lte=self.since,
            until__gte=self.since - datetime.timedelta(days=1))
        if qs.count() >= 1:  # should actually only be one; should be unique
            return qs.first().initial_connected_membership
        else:
            return self

    @property
    def is_active(self):
        """Is this membership currently active"""
        return self.until is None or self.until > timezone.now().date()

    def clean(self):
        if self.until and (not self.since or self.until < self.since):
            raise ValidationError(
                {'until': _("End date can't be before start date")})
        if self.until and self.until > timezone.now().date():
            raise ValidationError(
                {'until': _("End date can't be in the future")})

        if (self.since and self.group.since and
                self.since < self.group.since):
            raise ValidationError(
                {'since': _("Start date can't be before committee start date")}
                )
        if (self.since and self.group.until and
                self.since > self.group.until):
            raise ValidationError(
                {'since': _("Start date can't be after committee end date")})

        try:
            if self.until and self.group.board:
                raise ValidationError(
                    {'until': _("End date cannot be set for boards")})
        except Board.DoesNotExist:
            pass

    def validate_unique(self, *args, **kwargs):
        super().validate_unique(*args, **kwargs)
        # Check if a committee has more than one chair
        if self.chair:
            chairs = (MemberGroupMembership.objects
                      .filter(group=self.group,
                              chair=True))
            for chair in chairs:
                if chair.pk == self.pk:
                    continue
                if ((chair.until is None and
                        (self.until is None or self.until > chair.since)) or
                        (self.until is None and self.since < chair.until) or
                        (self.until and chair.until and
                            self.since < chair.until and
                            self.until > chair.since)):
                    raise ValidationError({
                        NON_FIELD_ERRORS:
                            _('There already is a '
                              'chair for this time period')})

        # check if this member is already in the committee in this period
        memberships = (MemberGroupMembership.objects
                       .filter(group=self.group,
                               member=self.member))
        for mship in memberships:
            if mship.pk == self.pk:
                continue
            if ((mship.until is None and
                    (self.until is None or self.until > mship.since)) or
                    (self.until is None and self.since < mship.until) or
                    (self.until and mship.until and
                        self.since < mship.until and
                        self.until > mship.since)):
                raise ValidationError({
                    'member': _('This member is already in the group for '
                                'this period')})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.member.is_staff = (self.member
                                .membergroupmembership_set
                                .exclude(until__lte=timezone.now().date())
                                .count()) >= 1
        self.member.save()

    def __str__(self):
        return "{} membership of {} since {}, until {}".format(self.member,
                                                               self.group,
                                                               self.since,
                                                               self.until)

    class Meta:
        verbose_name = _('group membership')
        verbose_name_plural = _('group memberships')


class Mentorship(models.Model):
    """Describe a mentorship during the orientation"""
    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        verbose_name=_('Member'),
    )
    year = models.IntegerField(validators=[MinValueValidator(1990)])

    def __str__(self):
        return _("{name} mentor in {year}").format(name=self.member,
                                                   year=self.year)

    class Meta:
        unique_together = ('member', 'year')
