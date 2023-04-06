from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from moneybirdsynchronization.moneybird import get_moneybird_api_service

from events.models import EventRegistration
from members.models import Member
from payments import payables
from payments.models import Payment
from pizzas.models import FoodOrder
from registrations.models import Registration, Renewal
from sales.models.order import Order
from thaliawebsite import settings


def financial_account_id_for_payment_type(payment_type):
    if payment_type == Payment.CARD:
        return settings.MONEYBIRD_PIN_FINANCIAL_ACCOUNT_ID
    if payment_type == Payment.CASH:
        return settings.MONEYBIRD_CASH_FINANCIAL_ACCOUNT_ID
    if payment_type == Payment.TPAY:
        return settings.MONEYBIRD_THALIAPAY_FINANCIAL_ACCOUNT_ID
    return None


def project_name_for_payable_model(obj):
    if isinstance(obj, EventRegistration):
        start_date = obj.event.start.strftime("%Y-%m-%d")
        return f"{obj.event.title} [{start_date}]"
    if isinstance(obj, FoodOrder):
        start_date = obj.food_event.event.start.strftime("%Y-%m-%d")
        return f"{obj.food_event.event.title} [{start_date}]"
    if isinstance(obj, Order):
        start_date = obj.shift.start.strftime("%Y-%m-%d")
        return f"{obj.shift} [{start_date}]"
    if isinstance(obj, (Registration, Renewal)):
        return None

    raise ValueError(f"Unknown payable model {obj}")


def date_for_payable_model(obj):
    if isinstance(obj, EventRegistration):
        return obj.event.start
    if isinstance(obj, FoodOrder):
        return obj.food_event.event.start
    if isinstance(obj, Order):
        return obj.shift.start
    if isinstance(obj, (Registration, Renewal)):
        return obj.created_at.date()

    raise ValueError(f"Unknown payable model {obj}")


def ledger_id_for_payable_model(obj):
    if isinstance(obj, (Registration, Renewal)):
        return settings.MONEYBIRD_CONTRIBUTION_LEDGER_ID
    return None


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
            return None
        data = {
            "contact": {
                "firstname": self.member.first_name,
                "lastname": self.member.last_name,
                "address1": self.member.profile.address_street,
                "address2": self.member.profile.address_street2,
                "zipcode": self.member.profile.address_postal_code,
                "city": self.member.profile.address_city,
                "country": self.member.profile.address_country,
                "send_invoices_to_email": self.member.email,
            }
        }
        if self.moneybird_id is not None:
            data["id"] = self.moneybird_id
        if settings.MONEYBIRD_MEMBER_PK_CUSTOM_FIELD_ID:
            data["contact"]["custom_fields_attributes"]["0"] = {
                "id": settings.MONEYBIRD_MEMBER_PK_CUSTOM_FIELD_ID,
                "value": self.member.pk,
            }
        return data

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


class MoneybirdExternalInvoice(models.Model):
    payable_model = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)
    payable_object = GenericForeignKey("payable_model", "object_id")

    moneybird_invoice_id = models.CharField(
        verbose_name=_("moneybird invoice id"),
        max_length=255,
        blank=True,
        null=True,
    )

    moneybird_details_attribute_id = models.CharField(
        verbose_name=_("moneybird details attribute id"),
        max_length=255,
        blank=True,
        null=True,
    )  # We need this id, so we can update the rows (otherwise, updates will create new rows without deleting).
    # We only support one attribute for now, so this is the easiest way to store it

    @property
    def payable(self):
        payable = payables.get_payable(self.payable_object)
        if payable is None:
            raise ValueError(f"Could not find payable for {self.payable_object}")
        return payable

    @classmethod
    def create_for_object(cls, obj):
        content_type = ContentType.objects.get_for_model(obj)
        return cls.objects.create(
            payable_model=content_type,
            object_id=obj.pk,
        )

    @classmethod
    def get_for_object(cls, obj):
        content_type = ContentType.objects.get_for_model(obj)
        try:
            return cls.objects.get(
                payable_model=content_type,
                object_id=obj.pk,
            )
        except cls.DoesNotExist:
            return None

    def to_moneybird(self):
        moneybird = get_moneybird_api_service()

        if self.payable.payment_payer is None:
            contact_id = settings.MONEYBIRD_UNKOWN_PAYER_CONTACT_ID
        else:
            moneybird_contact, created = MoneybirdContact.objects.get_or_create(
                member=self.payable.payment_payer
            )
            if created:
                response = moneybird.create_contact(moneybird_contact.to_moneybird())
                moneybird_contact.moneybird_id = response["id"]
                moneybird_contact.moneybird_version = response["version"]
                moneybird_contact.save()

            contact_id = moneybird_contact.moneybird_id

        invoice_date = date_for_payable_model(self.payable_object).strftime("%Y-%m-%d")

        project_name = project_name_for_payable_model(self.payable_object)

        project_id = moneybird.get_or_create_project(project_name)

        ledger_id = ledger_id_for_payable_model(self.payable_object)

        source_url = settings.BASE_URL + reverse(
            f"admin:{self.payable_object._meta.app_label}_{self.payable_object._meta.model_name}_change",
            args=(self.object_id,),
        )

        data = {
            "external_sales_invoice": {
                "contact_id": contact_id,
                "reference": self.payable.payment_topic,
                "date": invoice_date,
                "currency": "EUR",
                "prices_are_incl_tax": True,
                "details_attributes": [
                    {
                        "description": self.payable.payment_notes,
                        "price": str(self.payable.payment_amount),
                    },
                ],
            }
        }

        if source_url is not None:
            data["external_sales_invoice"]["source_url"] = source_url
        if project_id is not None:
            data["external_sales_invoice"]["details_attributes"][0][
                "project_id"
            ] = project_id
        if ledger_id is not None:
            data["external_sales_invoice"]["details_attributes"][0][
                "ledger_id"
            ] = ledger_id

        if self.moneybird_details_attribute_id is not None:
            data["external_sales_invoice"]["details_attributes"][0][
                "id"
            ] = self.moneybird_details_attribute_id

        if self.moneybird_invoice_id is not None:
            data["id"] = self.moneybird_invoice_id

        return data

    def __str__(self):
        return f"Moneybird external invoice for {self.payable_object}"

    class Meta:
        verbose_name = _("moneybird external invoice")
        verbose_name_plural = _("moneybird external invoices")
        unique_together = ("payable_model", "object_id")


class MoneybirdPayment(models.Model):
    payment = models.OneToOneField(
        "payments.Payment",
        on_delete=models.CASCADE,
        verbose_name=_("payment"),
        related_name="moneybird_payment",
    )

    moneybird_financial_statement_id = models.CharField(
        verbose_name=_("moneybird financial statement id"),
        max_length=255,
        blank=True,
        null=True,
    )

    moneybird_financial_mutation_id = models.CharField(
        verbose_name=_("moneybird financial mutation id"),
        max_length=255,
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"Moneybird payment for {self.payment}"

    def to_moneybird(self):
        data = {
            "date": self.payment.created_at.strftime("%Y-%m-%d"),
            "message": f"{self.payment.pk}; {self.payment.type} by {self.payment.paid_by}; {self.payment.notes}; processed by {self.payment.processed_by or '?'} at {self.payment.created_at:'%Y-%m-%d $h:$m:$s'}.",
            "amount": str(self.payment.amount),
        }
        if self.moneybird_financial_mutation_id is not None:
            data["financial_mutation_id"] = self.moneybird_financial_mutation_id
            data["financial_account_id"] = financial_account_id_for_payment_type(
                self.payment.type
            )

        return data

    class Meta:
        verbose_name = _("moneybird payment")
        verbose_name_plural = _("moneybird payments")
