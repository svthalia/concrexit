"""The models defined by the activemembers package."""
import datetime
import logging

from django.conf import settings
from django.contrib.admin import display as admin_display
from django.contrib.auth.models import Permission
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from thumbnails.fields import ImageField
from tinymce.models import HTMLField

from thaliawebsite.storage.backend import get_public_storage
from utils.snippets import overlaps

logger = logging.getLogger(__name__)


class ActiveMemberGroupManager(models.Manager):
    """Returns active objects only sorted by the localized name."""

    def get_queryset(self):
        return super().get_queryset().exclude(active=False).order_by("name")


class MemberGroup(models.Model):
    """Describes a groups of members."""

    objects = models.Manager()
    active_objects = ActiveMemberGroupManager()

    name = models.CharField(max_length=40, verbose_name=_("Name"), unique=True)

    description = HTMLField(verbose_name=_("Description"))

    photo = ImageField(
        verbose_name=_("Image"),
        upload_to="committeephotos/",
        storage=get_public_storage,
        null=True,
        blank=True,
    )

    members = models.ManyToManyField(
        "members.Member", through="activemembers.MemberGroupMembership"
    )

    permissions = models.ManyToManyField(
        Permission,
        verbose_name=_("permissions"),
        blank=True,
        related_name="permissions_groups",
    )

    chair_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_("chair permissions"),
        blank=True,
        help_text="Permissions only for certain members of a committee",
        related_name="chair_permissions_groups",
    )

    since = models.DateField(
        _("founded in"),
        null=True,
        blank=True,
    )

    until = models.DateField(
        _("existed until"),
        null=True,
        blank=True,
    )

    active = models.BooleanField(
        default=False,
        help_text=_(
            "This should only be unchecked if the committee has been "
            "dissolved. The websites assumes that any committees on it"
            " existed at some point."
        ),
    )

    contact_email = models.EmailField(
        _("contact email address"),
        blank=True,
        null=True,
    )

    contact_mailinglist = models.OneToOneField(
        "mailinglists.MailingList",
        verbose_name=_("contact mailing list"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    display_members = models.BooleanField(
        default=False,
    )

    @property
    @admin_display(description=_("email"))
    def contact_address(self):
        if self.contact_mailinglist:
            return f"{self.contact_mailinglist.name}@{settings.SITE_DOMAIN}"
        return self.contact_email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.photo:
            self._orig_image = self.photo.name
        else:
            self._orig_image = None

    def save(self, **kwargs):
        super().save(**kwargs)
        storage = self.photo.storage

        if self._orig_image and self._orig_image != self.photo.name:
            storage.delete(self._orig_image)
            self._orig_image = None

    def delete(self, using=None, keep_parents=False):
        if self.photo.name:
            self.photo.delete()
        return super().delete(using, keep_parents)

    def clean(self):
        if (
            self.contact_email is not None and self.contact_mailinglist is not None
        ) or (self.contact_email is None and self.contact_mailinglist is None):
            raise ValidationError(
                {
                    "contact_email": _(
                        "Please use either the mailing list or email address option."
                    ),
                    "contact_mailinglist": _(
                        "Please use either the mailing list or email address option."
                    ),
                }
            )

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        try:
            return self.board.get_absolute_url()
        except self.DoesNotExist:
            try:
                return self.committee.get_absolute_url()
            except self.DoesNotExist:
                try:
                    return self.society.get_absolute_url()
                except self.DoesNotExist:
                    raise NotImplementedError(
                        f"get_absolute_url() not implemented for {self.__class__.__name__}"
                    )

    class Meta:
        verbose_name = _("member group")
        verbose_name_plural = _("member groups")
        # ordering is done in the manager, to sort on a translated field


class Committee(MemberGroup):
    """Describes a committee, which is a type of MemberGroup."""

    objects = models.Manager()
    active_objects = ActiveMemberGroupManager()

    def get_absolute_url(self):
        return reverse("activemembers:committee", args=[str(self.pk)])

    class Meta:
        verbose_name = _("committee")
        verbose_name_plural = _("committees")
        # ordering is done in the manager, to sort on a translated field


class Society(MemberGroup):
    """Describes a society, which is a type of MemberGroup."""

    objects = models.Manager()
    active_objects = ActiveMemberGroupManager()

    def get_absolute_url(self):
        return reverse("activemembers:society", args=[str(self.pk)])

    class Meta:
        verbose_name = _("society")
        verbose_name_plural = _("societies")
        # ordering is done in the manager, to sort on a translated field


class Board(MemberGroup):
    """Describes a board, which is a type of MemberGroup."""

    class Meta:
        verbose_name = _("board")
        verbose_name_plural = _("boards")
        ordering = ["-since"]

    def save(self, **kwargs):
        self.active = True
        super().save(**kwargs)

    def get_absolute_url(self):
        return reverse(
            "activemembers:board", args=[str(self.since.year), str(self.until.year)]
        )

    def validate_unique(self, **kwargs):
        super().validate_unique(**kwargs)
        boards = Board.objects.all()
        if self.since is not None:
            if overlaps(self, boards, can_equal=False):
                raise ValidationError(
                    {
                        "since": _("A board already exists for those years"),
                        "until": _("A board already exists for those years"),
                    }
                )


class ActiveMembershipManager(models.Manager):
    """Custom manager that gets the currently active membergroup memberships."""

    def get_queryset(self):
        return super().get_queryset().exclude(until__lt=timezone.now().date())


class MemberGroupMembership(models.Model):
    """Describes a group membership."""

    objects = models.Manager()
    active_objects = ActiveMembershipManager()

    member = models.ForeignKey(
        "members.Member",
        on_delete=models.CASCADE,
        verbose_name=_("Member"),
    )

    group = models.ForeignKey(
        MemberGroup,
        on_delete=models.CASCADE,
        verbose_name=_("Group"),
    )

    since = models.DateField(
        verbose_name=_("Member since"),
        help_text=_("The date this member joined in this role"),
        default=datetime.date.today,
    )

    until = models.DateField(
        verbose_name=_("Member until"),
        help_text=_("A member until this time (can't be in the future)."),
        blank=True,
        null=True,
    )

    chair = models.BooleanField(
        verbose_name=_("Chair of the group"),
        help_text=_("There can only be one chair at a time!"),
        default=False,
    )

    has_chair_permissions = models.BooleanField(
        verbose_name=_("Person with chair permissions"),
        help_text=_("Give this member chair permission"),
        default=False,
    )

    role = models.CharField(
        _("role"),
        help_text=_("The role of this member"),
        max_length=255,
        blank=True,
        null=True,
    )

    @property
    def initial_connected_membership(self):
        """Find the oldest membership directly connected to the current one."""
        qs = MemberGroupMembership.objects.filter(
            group=self.group,
            member=self.member,
            until__lte=self.since,
            until__gte=self.since - datetime.timedelta(days=1),
        )
        if qs.exists():  # should only be one; should be unique
            return qs.first().initial_connected_membership
        return self

    @property
    def latest_connected_membership(self):
        """Find the newest membership directly connected to the current one.

        (thus the membership that started at the moment the current one ended).
        """
        if self.until:
            qs = MemberGroupMembership.objects.filter(
                group=self.group,
                member=self.member,
                since__lte=self.until,
                since__gte=self.until + datetime.timedelta(days=1),
            )
            if qs.exists():  # should only be one; should be unique
                return qs.last().latest_connected_membership
        return self

    @property
    def is_active(self):
        """Is this membership currently active."""
        return self.until is None or self.until > timezone.now().date()

    def clean(self):
        try:
            if self.until and (not self.since or self.until < self.since):
                raise ValidationError(
                    {"until": _("End date can't be before start date")}
                )
            if self.until and self.group.until and self.until > self.group.until:
                raise ValidationError(
                    {"until": _("End date can't be after the group end date")}
                )
            if self.since and self.group.since and self.since < self.group.since:
                raise ValidationError(
                    {"since": _("Start date can't be before group start date")}
                )
            if self.since and self.group.until and self.since > self.group.until:
                raise ValidationError(
                    {"since": _("Start date can't be after group end date")}
                )
        except MemberGroupMembership.group.RelatedObjectDoesNotExist:
            pass

    def validate_unique(self, **kwargs):
        try:
            super().validate_unique(**kwargs)
            # Check if a group has more than one chair
            if self.chair:
                chairs = MemberGroupMembership.objects.filter(
                    group=self.group, chair=True
                )
                if overlaps(self, chairs):
                    raise ValidationError(
                        {
                            NON_FIELD_ERRORS: _(
                                "There already is a chair for this time period"
                            )
                        }
                    )

            # check if this member is already in the group in this period
            memberships = MemberGroupMembership.objects.filter(
                group=self.group, member=self.member
            )
            if overlaps(self, memberships):
                raise ValidationError(
                    {"member": _("This member is already in the group for this period")}
                )

        except (
            MemberGroupMembership.member.RelatedObjectDoesNotExist,
            MemberGroupMembership.group.RelatedObjectDoesNotExist,
        ):
            pass

    def save(self, **kwargs):
        super().save(**kwargs)
        self.member.is_staff = self.member.membergroupmembership_set.exclude(
            until__lte=timezone.now().date()
        ).exists()
        self.member.save()

    def __str__(self):
        return _("{member} membership of {group} since {since}, until {until}").format(
            member=self.member, group=self.group, since=self.since, until=self.until
        )

    class Meta:
        verbose_name = _("group membership")
        verbose_name_plural = _("group memberships")


class Mentorship(models.Model):
    """Describe a mentorship during the orientation."""

    member = models.ForeignKey(
        "members.Member",
        on_delete=models.CASCADE,
        verbose_name=_("Member"),
    )
    year = models.IntegerField(validators=[MinValueValidator(1990)])

    def __str__(self):
        return _("{name} mentor in {year}").format(name=self.member, year=self.year)

    class Meta:
        unique_together = ("member", "year")
