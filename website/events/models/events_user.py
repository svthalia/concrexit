from django.db import models
from django.contrib.auth import get_user_model

from django.utils.translation import gettext_lazy as _


UserModel = get_user_model()


class EventsUser(UserModel):
    class Meta:
        verbose_name = _("Events user")
        verbose_name_plural = _("Events users")
        proxy = True

    def can_attend_events(self):
        return not self.blacklisted_events_user


class BlacklistedEventsUser(Member):
    class Meta:
        verbose_name = _("Blacklisted events user")
        verbose_name_plural = _("Blacklisted events users")

    user = models.OneToOneField(
        EventsUser,
        models.CASCADE,
        verbose_name=_("user"),
        related_name="blacklisted_events_user",
        blank=False,
        null=False,
    )

    remarks = models.TextField(
        verbose_name=_("Remarks"),
        help_text=_("Reason for blacklisting"),
        blank=True,
        null=True,
    )

    def __str__(self):
        return str(self.user)
