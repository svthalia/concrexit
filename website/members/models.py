from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


class Membership(models.Model):
    """This class describes membership data"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    membership_type = models.CharField(
        max_length=40,
        choices=(('benefactor', _('Benefactor')),
                 ('member', _('Member')),
                 ('honorary', _('Honorary Member'))),
    )
