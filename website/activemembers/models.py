import datetime
import logging

from django.contrib.auth.models import Permission
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from members.models import Member
from utils.translation import (ModelTranslateMeta, MultilingualField,
                               localize_attr_name)

logger = logging.getLogger(__name__)


class UnfilteredSortedManager(models.Manager):
    """Returns committees and boards, sorted by name"""
    def get_queryset(self):
        return (super().get_queryset()
                .order_by(localize_attr_name('name')))


class CommitteeManager(models.Manager):
    """Returns committees only"""
    def get_queryset(self):
        return (super().get_queryset()
                .exclude(board__is_board=True)
                .order_by(localize_attr_name('name')))


class ActiveCommitteeManager(models.Manager):
    """Returns active committees only"""
    def get_queryset(self):
        return (super().get_queryset()
                .exclude(board__is_board=True)
                .exclude(active=False)
                .order_by(localize_attr_name('name')))


class Committee(models.Model, metaclass=ModelTranslateMeta):
    """A committee"""

    unfiltered_objects = UnfilteredSortedManager()
    objects = CommitteeManager()
    active_committees = ActiveCommitteeManager()

    name = MultilingualField(
        models.CharField,
        max_length=40,
        verbose_name=_('Committee name'),
        unique=True,
    )

    description = MultilingualField(
        models.TextField,
        verbose_name=_('Description'),
    )

    photo = models.ImageField(
        verbose_name=_('Image'),
        upload_to='public/committeephotos/',
        null=True,
        blank=True,
    )

    members = models.ManyToManyField(
        Member,
        through='CommitteeMembership'
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

    contact_email = models.EmailField(_('contact email address'))

    wiki_namespace = models.CharField(
        _('Wiki namespace'),
        null=True,
        blank=True,
        max_length=50)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('activemembers:committee', args=[str(self.pk)])

    class Meta:
        verbose_name = _('committee')
        verbose_name_plural = _('committees')
        # ordering is done in the manager, to sort on a translated field


class BoardManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_board=True)


class Board(Committee):
    """ Because Board inherits from Committee, Django creates a OneToOneField
    linking the two models together. This can be accessed as usual;
    given a Committee or Board b, one can access b.board, which will either
    return the object b if b is a Board, or a Board.DoesNotExist exception.
    """
    objects = BoardManager()

    is_board = models.BooleanField(
        verbose_name=_('Is this a board'),
        default=True,
    )

    class Meta:
        ordering = ['-since']

    def get_absolute_url(self):
        return reverse('activemembers:board', args=[str(self.pk)])


class ActiveMembershipManager(models.Manager):
    """Get only active memberships"""
    def get_queryset(self):
        """Get the currently active committee memberships"""
        return super().get_queryset().exclude(until__lt=timezone.now().date())


class CommitteeMembership(models.Model, metaclass=ModelTranslateMeta):
    objects = models.Manager()
    active_memberships = ActiveMembershipManager()

    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        verbose_name=_('Member'),
    )

    committee = models.ForeignKey(
        Committee,
        on_delete=models.CASCADE,
        verbose_name=_('Committee'),
    )

    since = models.DateField(
        verbose_name=_('Committee member since'),
        help_text=_('The date this member joined the committee in this role'),
        default=datetime.date.today
    )

    until = models.DateField(
        verbose_name=_('Committee member until'),
        help_text=_("A member of this committee until this time "
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
    def is_active(self):
        """Is this membership currently active"""
        return self.until is None or self.until > timezone.now().date()

    def clean(self):
        """Validation"""
        if self.until and (not self.since or self.until < self.since):
            raise ValidationError(
                {'until': _("End date can't be before start date")})
        try:
            if self.until and self.committee.board:
                raise ValidationError(
                    {'until': _("End date cannot be set for boards")})
        except Board.DoesNotExist:
            pass

    def validate_unique(self, *args, **kwargs):
        """ Check uniqueness"""
        super().validate_unique(*args, **kwargs)
        # Check if a committee has more than one chair
        if self.chair:
            chairs = (CommitteeMembership.objects
                      .filter(committee=self.committee,
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
                        _('There already is a chair for this time period')})

        # check if this member is already in the committee in this period
        memberships = (CommitteeMembership.objects
                       .filter(committee=self.committee,
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
                    'member': _('This member is already in the committee for '
                                'this period')})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.member.user.is_staff = (
            self.member
            .committeemembership_set
            .exclude(
                until__lt=timezone.now().date())
            .count()) >= 1
        self.member.user.save()

    def __str__(self):
        return "{} membership of {} since {}, until {}".format(self.member,
                                                               self.committee,
                                                               self.since,
                                                               self.until)

    class Meta:
        verbose_name = _('committee membership')
        verbose_name_plural = _('committee memberships')


class Mentorship(models.Model):
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        verbose_name=_('Member'),
    )
    year = models.IntegerField(validators=MinValueValidator(1990))

    def __str__(self):
        return _("{name} mentor in {year}").format(name=self.member,
                                                   year=self.year)

    class Meta:
        unique_together = ('member', 'year')
