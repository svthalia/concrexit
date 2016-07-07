from django.utils import timezone

from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.contrib.auth.models import Permission
from django.db import models
from django.utils.translation import ugettext_lazy as _

from members.models import Member


class Committee(models.Model):
    """A committee"""

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

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('committee')
        verbose_name_plural = _('committees')


class ActiveMembershipManager(models.Manager):
    """Get only active memberships"""
    def get_queryset(self):
        """Get the currently active committee memberships"""
        return super().get_queryset().exclude(until__lt=timezone.now())


class CommitteeMembership(models.Model):
    active_memberships = ActiveMembershipManager()
    objects = models.Manager()

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
        auto_now_add=True,
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

    @property
    def is_active(self):
        """Is this membership currently active"""
        return self.until is None or self.until > timezone.now()

    def clean(self):
        """Validation"""
        if self.until and self.until > timezone.now():
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
                  .filter(chair=True)
                  .count())
        if chairs >= 1 and self.chair:
            raise ValidationError({
                NON_FIELD_ERRORS:
                _('This committee already has a chair')})

        # check if this member is already in the committee
        members = (self.committee.members
                   .filter(pk=self.member.pk)
                   .count())
        if members >= 1:
            raise ValidationError({
                'member': _('This member is already in the committee')})

    def __str__(self):
        return "{} membership of {} since {}".format(self.member,
                                                     self.committee,
                                                     self.since)

    class Meta:
        verbose_name = _('committee membership')
        verbose_name_plural = _('committee memberships')
