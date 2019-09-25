"""The models defined by the mailinglists package"""
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from activemembers.models import MemberGroup, Board
from members.models import Member
from utils.snippets import datetime_to_lectureyear


def get_automatic_mailinglists():
    """Return mailing list names that should be generated automatically."""
    lectureyear = datetime_to_lectureyear(timezone.now())
    list_names = ['leden', 'members', 'begunstigers', 'benefactors',
                  'ereleden', 'honorary', 'mentors', 'activemembers',
                  'commissievoorzitters', 'committeechairs',
                  'optin', 'oldboards', 'oudbesturen']
    if Board.objects.exists():
        for year in range(Board.objects.earliest('since').since.year,
                          lectureyear):
            board = Board.objects.get(since__year=year)
            if board is not None:
                years = str(board.since.year)[-2:] + str(board.until.year)[-2:]
                list_names += [f'bestuur{years}', f'board{years}']
    return list_names


class MailingList(models.Model):
    """Model describing mailing lists."""

    name = models.CharField(
        verbose_name=_("Name"),
        max_length=100,
        validators=[validators.RegexValidator(
            regex=r'^[a-zA-Z0-9]+$',
            message=_('Enter a simpler name'))
        ],
        unique=True,
        help_text=_('Enter the name for the list (i.e. name@thalia.nu).'),
    )

    prefix = models.CharField(
        verbose_name=_("Prefix"),
        blank=True,
        max_length=200,
        help_text=_('Enter a prefix that should be prefixed to subjects '
                    'of all emails sent via this mailinglist.'),
    )

    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_('Write a description for the mailinglist.'),
    )

    archived = models.BooleanField(
        verbose_name=_("Archived"),
        default=True,
        help_text=_('Indicate whether an archive should be kept.')
    )

    moderated = models.BooleanField(
        verbose_name=_("Moderated"),
        default=False,
        help_text=_('Indicate whether emails to the list require approval.')
    )

    members = models.ManyToManyField(
        Member,
        verbose_name=_("Members"),
        blank=True,
        help_text=_('Select individual members to include in the list.'),
    )

    member_groups = models.ManyToManyField(
        MemberGroup,
        verbose_name=_("Member groups"),
        help_text=_('Select entire groups to include in the list.'),
        blank=True,
    )

    autoresponse_enabled = models.BooleanField(
        verbose_name=_("Automatic response enabled"),
        default=False,
        help_text=_('Indicate whether emails will get an automatic response.')
    )

    autoresponse_text = models.TextField(
        verbose_name=_("Autoresponse text"),
        null=True,
        blank=True,
    )

    def all_addresses(self):
        """Return all addresses subscribed to this mailing list."""
        for member in self.members.all():
            yield member.email

        for group in self.member_groups.all().prefetch_related("members"):
            for member in group.members.exclude(
                    membergroupmembership__until__lt=timezone.now().date()):
                yield member.email

        for verbatimaddress in self.addresses.all():
            yield verbatimaddress.address

    def clean(self):
        """Validate the mailing list."""
        super().clean()
        if (ListAlias.objects
                .filter(alias=self.name).count() > 0 or
                self.name in get_automatic_mailinglists()):
            raise ValidationError({
                'name': _("%(model_name)s with this "
                          "%(field_label)s already exists.") % {
                             'model_name': _("Mailing list"),
                             'field_label': _("List alias")
                         }
            })

        if not self.autoresponse_text and self.autoresponse_enabled:
            raise ValidationError({
                'autoresponse_text': _('Enter a text for the auto response.')
            })

    def __str__(self):
        """Return the name of the mailing list."""
        return self.name


class VerbatimAddress(models.Model):
    """Model that describes an email address subscribed to a mailing list."""

    address = models.EmailField(
        verbose_name=_("Email address"),
        help_text=_('Enter an explicit email address to include in the list.'),
    )

    mailinglist = models.ForeignKey(MailingList,
                                    verbose_name=_("Mailing list"),
                                    on_delete=models.CASCADE,
                                    related_name='addresses')

    def __str__(self):
        """Return the address."""
        return self.address

    class Meta:
        """Meta class for VerbatimAddress."""

        verbose_name = _("Verbatim address")
        verbose_name_plural = _("Verbatim addresses")


class ListAlias(models.Model):
    """Model describing an alias of a mailing list."""

    alias = models.CharField(
        verbose_name=_("Alternative name"),
        max_length=100,
        validators=[validators.RegexValidator(
            regex=r'^[a-zA-Z0-9]+$',
            message=_('Enter a simpler name'))
        ],
        unique=True,
        help_text=_('Enter an alternative name for the list.'),
    )
    mailinglist = models.ForeignKey(MailingList,
                                    verbose_name=_("Mailing list"),
                                    on_delete=models.CASCADE,
                                    related_name='aliasses')

    def clean(self):
        """Validate the alias."""
        super().clean()
        if (MailingList.objects
                .filter(name=self.alias).count() > 0 or
                self.alias in get_automatic_mailinglists()):
            raise ValidationError({
                'alias': _("%(model_name)s with this "
                           "%(field_label)s already exists.") % {
                    'model_name': _("Mailing list"),
                    'field_label': _("Name")
                }
            })

    def __str__(self):
        """Return a string representation of the alias and mailing list."""
        return (_("List alias {alias} for {list}")
                .format(alias=self.alias,
                        list=self.mailinglist.name))

    class Meta:
        """Meta class for ListAlias."""

        verbose_name = _("List alias")
        verbose_name_plural = _("List aliasses")
