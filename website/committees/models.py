import datetime
import logging

from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.contrib.auth.models import Permission
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from members.models import Member


logger = logging.getLogger(__name__)


class CommitteeManager(models.Manager):
    """Returns committees only"""
    def get_queryset(self):
        return (super().get_queryset()
                .exclude(board__is_board=True))


class ActiveCommitteeManager(models.Manager):
    """Returns active committees only"""
    def get_queryset(self):
        return (super().get_queryset()
                .exclude(board__is_board=True)
                .exclude(until__lt=timezone.now().date()))


class Committee(models.Model):
    """A committee"""

    unfiltered_objects = models.Manager()
    objects = CommitteeManager()
    active_committees = ActiveCommitteeManager()

    name = models.CharField(
        max_length=40,
        verbose_name=_('Committee name'),
        unique=True,
    )

    description = models.TextField(
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

    contact_email = models.EmailField(_('contact email address'))

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('committees:committee', args=[str(self.pk)])

    class Meta:
        verbose_name = _('committee')
        verbose_name_plural = _('committees')


class BoardManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_board=True)


class Board(Committee):
    objects = BoardManager()

    is_board = models.BooleanField(
        verbose_name=_('Is this a board'),
        default=True,
    )

    def get_absolute_url(self):
        return reverse('committees:board', args=[str(self.pk)])


class ActiveMembershipManager(models.Manager):
    """Get only active memberships"""
    def get_queryset(self):
        """Get the currently active committee memberships"""
        return super().get_queryset().exclude(until__lt=timezone.now().date())


class CommitteeMembership(models.Model):
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

    role = models.CharField(
        _('role'),
        help_text=_('The role of this member'),
        max_length=255,
        blank=True,
        null=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.pk is None:
            self._was_chair = bool(self.chair)
        else:
            self._was_chair = False

    @property
    def is_active(self):
        """Is this membership currently active"""
        return self.until is None or self.until > timezone.now().date()

    def clean(self):
        """Validation"""
        if self.until and self.until > timezone.now().date():
            raise ValidationError({
                'until': _("Membership expiration date can't be in the future:"
                           " '{}'").format(self.until)
            })

        if self.until and (not self.since or self.until < self.since):
            raise ValidationError(
                {'until': _("End date can't be before start date")})

    def validate_unique(self, *args, **kwargs):
        """ Check uniqueness"""
        super().validate_unique(*args, **kwargs)
        # Check if a committee has more than one chair
        chairs = (CommitteeMembership.active_memberships
                  .filter(committee=self.committee)
                  .exclude(member=self.member)
                  .filter(chair=True)
                  .count())
        if chairs >= 1 and self.chair:
            raise ValidationError({
                NON_FIELD_ERRORS:
                _('This committee already has a chair')})

        # check if this member is already in the committee
        if self.pk is None:
            until = self.until if self.until else timezone.now().date()
            members = (CommitteeMembership.active_memberships
                       .filter(committee=self.committee, member=self.member)
                       .count())
            memberships = (CommitteeMembership.objects.filter(
                           committee=self.committee,
                           member=self.member,
                           since__lte=until,
                           until__gte=self.since)
                           .count())

            if members >= 1 and until >= timezone.now().date():
                raise ValidationError({
                    'member': _('This member is already in the committee')})
            elif memberships > 0:
                raise ValidationError({
                    'member': _('This member is already in the committee for '
                                'this period')})

    def save(self, *args, **kwargs):
        """Save the instance"""
        # If the chair changed and we're still active, we create a new instance
        # Inactive instances should be handled manually
        if (self.pk is not None and self._was_chair != self.chair and
                not self.until):
            logger.info("Creating new membership instance")
            self.until = timezone.now().date()
            super().save(*args, **kwargs)
            self.pk = None  # forces INSERT
            self.since = self.until  # Set since date to older expiration
            self.until = None
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Deactivates active memberships, deletes inactive ones"""
        if self.is_active:
            self.until = timezone.now().date()
            self.save()
        else:
            super().delete(*args, **kwargs)

    def __str__(self):
        return "{} membership of {} since {}".format(self.member,
                                                     self.committee,
                                                     self.since)

    class Meta:
        verbose_name = _('committee membership')
        verbose_name_plural = _('committee memberships')


class Mentorship(models.Model):
    members = models.ManyToManyField(Member)
    year = models.IntegerField(unique=True)

    def __str__(self):
        return _("Mentor introduction {year}").format(year=self.year)
