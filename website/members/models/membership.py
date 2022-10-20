from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from utils.snippets import overlaps


class Membership(models.Model):
    MEMBER = "member"
    BENEFACTOR = "benefactor"
    HONORARY = "honorary"

    MEMBERSHIP_TYPES = (
        (MEMBER, _("Member")),
        (BENEFACTOR, _("Benefactor")),
        (HONORARY, _("Honorary Member")),
    )

    type = models.CharField(
        max_length=40,
        choices=MEMBERSHIP_TYPES,
        verbose_name=_("Membership type"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_("User"),
    )

    since = models.DateField(
        verbose_name=_("Membership since"),
        help_text=_("The date the member started holding this membership."),
        default=timezone.now,
    )

    until = models.DateField(
        verbose_name=_("Membership until"),
        help_text=_("The date the member stops holding this membership."),
        blank=True,
        null=True,
    )

    def __str__(self):
        s = _("Membership of type {} for {} ({}) starting {}").format(
            self.get_type_display(),
            self.user.get_full_name(),
            self.user.username,
            self.since,
        )
        if self.until is not None:
            s += pgettext_lazy("Membership until x", " until {}").format(self.until)
        return s

    def clean(self):
        super().clean()

        errors = {}
        if self.until and (not self.since or self.until < self.since):
            raise ValidationError({"until": _("End date can't be before start date")})

        if self.since is not None:
            memberships = self.user.membership_set.all()
            if overlaps(self, memberships):
                errors.update(
                    {
                        "since": _("A membership already exists for that period"),
                        "until": _("A membership already exists for that period"),
                    }
                )

        if errors:
            raise ValidationError(errors)

    def is_active(self):
        return not self.until or self.until > timezone.now().date()
