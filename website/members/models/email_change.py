import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class EmailChange(models.Model):
    created_at = models.DateTimeField(_("created at"), default=timezone.now)

    member = models.ForeignKey(
        "members.Member",
        on_delete=models.CASCADE,
        verbose_name=_("member"),
    )

    email = models.EmailField(_("email"), max_length=254)

    verify_key = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    confirm_key = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    verified = models.BooleanField(
        _("verified"), default=False, help_text=_("the new email address is valid")
    )
    confirmed = models.BooleanField(
        _("confirmed"), default=False, help_text=_("the old email address was checked")
    )

    def __str__(self):
        return _(
            "Email change request for {} to {} "
            "created at {} "
            "(confirmed: {}, verified: {})."
        ).format(
            self.member, self.email, self.created_at, self.confirmed, self.verified
        )

    @property
    def completed(self):
        return self.verified and self.confirmed

    def clean(self):
        super().clean()

        if any(domain in self.email for domain in settings.EMAIL_DOMAIN_BLACKLIST):
            raise ValidationError(
                {
                    "email": _(
                        "You cannot use an email address "
                        "from this domain for your account."
                    )
                }
            )

        if self.email == self.member.email:
            raise ValidationError({"email": _("Please enter a new email address.")})
