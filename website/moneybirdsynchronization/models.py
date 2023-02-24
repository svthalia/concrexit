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
    moneybird_id = models.IntegerField(
        _("Moneybird ID"), 
        null=True, 
        blank=True
    )
    moneybird_version = models.IntegerField(
        _("Moneybird version"),
        null=True,
        blank=True,
    )

    def to_moneybird(self):
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
                    "0":{
                        "id": 380500576947930894,
                        "value": self.member.pk,
                        }
                    },
            }
        }

    def get_moneybird_info(self):
        return {'id': self.moneybird_id, 'version': self.moneybird_version, 'pk': self.member.pk}

