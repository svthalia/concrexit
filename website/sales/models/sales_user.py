from django.utils.translation import gettext_lazy as _

from members.models import Member


class SalesUser(Member):
    class Meta:
        verbose_name = _("Sales user")
        verbose_name_plural = _("Sales users")
        proxy = True
