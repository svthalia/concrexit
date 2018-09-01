from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from activemembers.models import MemberGroup
from members.models import Member


class MailingList(models.Model):
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

    committees = models.ManyToManyField(
        MemberGroup,
        verbose_name=_("Committees"),
        help_text=_('Select entire committees to include in the list.'),
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
        for member in self.members.all():
            yield member.email

        for committee in self.committees.all().prefetch_related("members"):
            for member in committee.members.exclude(
                    committeemembership__until__lt=timezone.now().date()):
                yield member.email

        for verbatimaddress in self.addresses.all():
            yield verbatimaddress.address

    def clean(self):
        super().clean()
        if (ListAlias.objects
                .filter(alias=self.name).count() > 0):
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
        return self.name


class VerbatimAddress(models.Model):
    address = models.EmailField(
        verbose_name=_("Email address"),
        help_text=_('Enter an explicit email address to include in the list.'),
    )

    mailinglist = models.ForeignKey(MailingList,
                                    verbose_name=_("Mailing list"),
                                    on_delete=models.CASCADE,
                                    related_name='addresses')

    def __str__(self):
        return self.address

    class Meta:
        verbose_name = _("Verbatim address")
        verbose_name_plural = _("Verbatim addresses")


class ListAlias(models.Model):
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
        super().clean()
        if (MailingList.objects
                .filter(name=self.alias).count() > 0):
            raise ValidationError({
                'alias': _("%(model_name)s with this "
                           "%(field_label)s already exists.") % {
                    'model_name': _("Mailing list"),
                    'field_label': _("Name")
                }
            })

    class Meta:
        verbose_name = _("List alias")
        verbose_name_plural = _("List aliasses")
