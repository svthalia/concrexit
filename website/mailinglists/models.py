from django.core import validators
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from activemembers.models import Committee
from members.models import Member


class MailingList(models.Model):
    name = models.CharField(max_length=100,
                            validators=[validators.RegexValidator(
                                        regex=r'^[a-zA-Z0-9]+$',
                                        message=_('Enter a simpler name'))
                                        ],
                            )
    prefix = models.CharField(max_length=200)
    archived = models.BooleanField(default=True)
    moderated = models.BooleanField(default=False)
    members = models.ManyToManyField(Member, blank=True)
    committees = models.ManyToManyField(Committee, blank=True)

    def all_addresses(self):
        for member in self.members.all():
            yield member.user.email

        for committee in self.committees.all().prefetch_related("members"):
            for member in committee.members.exclude(
                    committeemembership__until__lt=timezone.now().date()):
                yield member.user.email

        for address in self.addresses.all():
            yield address

    def __str__(self):
        return self.name


class VerbatimAddress(models.Model):
    address = models.EmailField()
    mailinglist = models.ForeignKey(MailingList,
                                    on_delete=models.CASCADE,
                                    related_name='addresses')

    def __str__(self):
        return self.address


class ListAlias(models.Model):
    alias = models.CharField(max_length=100,
                             validators=[validators.RegexValidator(
                                         regex=r'^[a-zA-Z0-9]+$',
                                         message=_('Enter a simpler name'))
                                         ],
                             )
    mailinglist = models.ForeignKey(MailingList,
                                    on_delete=models.CASCADE,
                                    related_name='aliasses')
