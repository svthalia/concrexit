from django.db import models

from members.models import Member
from committees.models import Committee


class MailingList(models.Model):
    name = models.EmailField()
    prefix = models.CharField(max_length=200)
    archived = models.BooleanField(default=True)
    moderated = models.BooleanField(default=False)
    members = models.ManyToManyField(Member, blank=True)
    committees = models.ManyToManyField(Committee, blank=True)

    def all_addresses(self):
        for member in self.members.all():
            yield member.email

        for committee in self.committees.all().prefetch_related("members"):
            for member in committee.members.all():
                yield member.email

        for address in self.addresses.all():
            yield address

    def __str__(self):
        return self.name


class VerbatimAddress(models.Model):
    address = models.EmailField()
    mailinglist = models.ForeignKey(MailingList, related_name='addresses')


class ListAlias(models.Model):
    alias = models.EmailField()
    mailinglist = models.ForeignKey(MailingList, related_name='aliasses')
