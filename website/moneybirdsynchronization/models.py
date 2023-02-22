from django.db import models
from django.utils.translation import gettext_lazy as _

from members.models import Member

class Contact(models.Model):
    member = models.OneToOneField(
        Member,
        on_delete=models.CASCADE,
        verbose_name=_("member"),
        null=True,
        blank=True,
    )
    moneybird_id = models.CharField(
        _("Moneybird ID"), 
        max_length=255, 
        null=True, 
        blank=True
    )

