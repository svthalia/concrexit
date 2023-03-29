from django.db import models
from django.utils.translation import gettext_lazy as _

from members.models import Member
from thaliawebsite import settings


class MoneybirdContact(models.Model):
    member = models.OneToOneField(
        Member,
        on_delete=models.CASCADE,
        verbose_name=_("member"),
        related_name="moneybird_contact",
        null=True,
        blank=True,
    )
    moneybird_id = models.IntegerField(_("Moneybird ID"), null=True, blank=True)
    moneybird_version = models.IntegerField(
        _("Moneybird version"),
        null=True,
        blank=True,
    )

    def to_moneybird(self):
        if self.member.profile is None:
            return {}
        return {
            "contact": {
                "firstname": self.member.first_name,
                "lastname": self.member.last_name,
                "address1": self.member.profile.address_street,
                "address2": self.member.profile.address_street2,
                "zipcode": self.member.profile.address_postal_code,
                "city": self.member.profile.address_city,
                "country": self.member.profile.address_country,
                "send_invoices_to_email": self.member.email,
                "custom_fields_attributes": {
                    "0": {
                        "id": settings.MONEYBIRD_CUSTOM_FIELD_ID,
                        "value": self.member.pk,
                    }
                },
            }
        }

    def get_moneybird_info(self):
        return {
            "id": self.moneybird_id,
            "version": self.moneybird_version,
            "pk": self.member.pk,
        }

    def __str__(self):
        return f"Moneybird contact for {self.member}"
    
    class Meta:
        verbose_name = _("moneybird contact")
        verbose_name_plural = _("moneybird contacts")