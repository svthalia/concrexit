import datetime
from typing import Optional, Union

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from events.models import EventRegistration
from members.models import Member
from moneybirdsynchronization.moneybird import get_moneybird_api_service
from payments.models import BankAccount, Payment
from payments.payables import payables
from pizzas.models import FoodOrder
from registrations.models import Registration, Renewal
from sales.models.order import Order
from thaliawebsite import settings


def datetime_to_membership_period(date):
    """Convert a :class:`~datetime.date` to a period that corresponds with the current membership period."""
    start_date = date
    if start_date.month == 8:
        start_date = start_date.replace(month=9, day=1)
    end_date = start_date.replace(month=8, day=31)
    if start_date.month > 8:
        end_date = end_date.replace(year=start_date.year + 1)
    return f"{start_date.strftime('%Y%m%d')}..{end_date.strftime('%Y%m%d')}"


def financial_account_id_for_payment_type(payment_type) -> Optional[int]:
    if payment_type == Payment.CARD:
        return settings.MONEYBIRD_CARD_FINANCIAL_ACCOUNT_ID
    if payment_type == Payment.CASH:
        return settings.MONEYBIRD_CASH_FINANCIAL_ACCOUNT_ID
    if payment_type == Payment.TPAY:
        return settings.MONEYBIRD_TPAY_FINANCIAL_ACCOUNT_ID
    return None


def project_name_for_payable_model(obj) -> Optional[str]:
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


def date_for_payable_model(obj) -> Union[datetime.datetime, datetime.date]:
    if isinstance(obj, EventRegistration):
        return obj.event.start
    if isinstance(obj, FoodOrder):
        return obj.food_event.event.start
    if isinstance(obj, Order):
        return obj.shift.start
    if isinstance(obj, (Registration, Renewal)):
        return obj.created_at.date()

    raise ValueError(f"Unknown payable model {obj}")


def ledger_id_for_payable_model(obj) -> Optional[int]:
    if isinstance(obj, (Registration, Renewal)):
        return settings.MONEYBIRD_CONTRIBUTION_LEDGER_ID
    return None


class MoneybirdProject(models.Model):
    name = models.CharField(
        _("Name"),
        max_length=255,
        blank=False,
        null=False,
        unique=True,
        db_index=True,
    )

    moneybird_id = models.CharField(
        _("Moneybird ID"),
        max_length=255,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("moneybird project")
        verbose_name_plural = _("moneybird projects")

    def __str__(self):
        return f"Moneybird project {self.name}"

    def to_moneybird(self):
        return {
            "project": {
                "name": self.name,
            }
        }


class MoneybirdContact(models.Model):
    member = models.OneToOneField(
        Member,
        on_delete=models.CASCADE,
        verbose_name=_("member"),
        related_name="moneybird_contact",
        null=True,
        blank=True,
    )
    moneybird_id = models.CharField(
        _("Moneybird ID"),
        max_length=255,
        blank=True,
        null=True,
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
                "customer_id": f"C-{self.member.pk}",
            }
        }
        bank_account = BankAccount.objects.filter(owner=self.member).last()
        if bank_account:
            data["contact"]["sepa_iban"] = bank_account.iban
            data["contact"]["sepa_bic"] = bank_account.bic or ""
            data["contact"][
                "sepa_iban_account_name"
            ] = f"{bank_account.initials} {bank_account.last_name}"
            if bank_account.valid:
                data["contact"]["sepa_active"] = True
                data["contact"]["sepa_mandate_id"] = bank_account.mandate_no
                data["contact"]["sepa_mandate_date"] = bank_account.valid_from.strftime(
                    "%Y-%m-%d"
                )
                data["contact"]["sepa_sequence_type"] = "RCUR"
            else:
                data["contact"]["sepa_active"] = False
        else:
            data["contact"]["sepa_iban_account_name"] = ""
            data["contact"]["sepa_iban"] = ""
            data["contact"]["sepa_bic"] = ""
            data["contact"]["sepa_active"] = False
        if self.moneybird_id is not None:
            data["id"] = self.moneybird_id
        if settings.MONEYBIRD_MEMBER_PK_CUSTOM_FIELD_ID:
            data["contact"]["custom_fields_attributes"] = {}
            data["contact"]["custom_fields_attributes"]["0"] = {
                "id": settings.MONEYBIRD_MEMBER_PK_CUSTOM_FIELD_ID,
                "value": self.member.pk,
            }
        return data

    def get_moneybird_info(self):
        return {
            "id": self.moneybird_id,
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
            contact_id = settings.MONEYBIRD_UNKNOWN_PAYER_CONTACT_ID
        else:
            moneybird_contact, __ = MoneybirdContact.objects.get_or_create(
                member=self.payable.payment_payer
            )
            if moneybird_contact.moneybird_id is None:
                # I know this is ugly, but I don't want to totally refactor the app.
                from moneybirdsynchronization.services import create_or_update_contact

                moneybird_contact = create_or_update_contact(moneybird_contact.member)

            contact_id = moneybird_contact.moneybird_id

        invoice_date = date_for_payable_model(self.payable_object).strftime("%Y-%m-%d")

        project_name = project_name_for_payable_model(self.payable_object)

        project_id = None
        if project_name is not None:
            project, __ = MoneybirdProject.objects.get_or_create(name=project_name)
            if project.moneybird_id is None:
                response = moneybird.create_project(project.to_moneybird())
                project.moneybird_id = response["id"]
                project.save()

            project_id = project.moneybird_id

        ledger_id = ledger_id_for_payable_model(self.payable_object)

        source_url = settings.BASE_URL + reverse(
            f"admin:{self.payable_object._meta.app_label}_{self.payable_object._meta.model_name}_change",
            args=(self.object_id,),
        )

        data = {
            "external_sales_invoice": {
                "contact_id": int(contact_id),
                "reference": f"{self.payable.payment_topic} [{self.payable.model.pk}]",
                "source": f"Concrexit ({settings.SITE_DOMAIN})",
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
            data["external_sales_invoice"]["details_attributes"][0]["project_id"] = int(
                project_id
            )
        if ledger_id is not None:
            data["external_sales_invoice"]["details_attributes"][0]["ledger_id"] = int(
                ledger_id
            )

        if self.moneybird_details_attribute_id is not None:
            data["external_sales_invoice"]["details_attributes"][0]["id"] = int(
                self.moneybird_details_attribute_id
            )

        return data

    def __str__(self):
        return f"Moneybird external invoice for {self.payable_object}"

    class Meta:
        verbose_name = _("moneybird external invoice")
        verbose_name_plural = _("moneybird external invoices")
        unique_together = ("payable_model", "object_id")


class MoneybirdSalesInvoice(models.Model):
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
            contact_id = settings.MONEYBIRD_UNKNOWN_PAYER_CONTACT_ID
        else:
            moneybird_contact, __ = MoneybirdContact.objects.get_or_create(
                member=self.payable.payment_payer
            )
            if moneybird_contact.moneybird_id is None:
                # I know this is ugly, but I don't want to totally refactor the app.
                from moneybirdsynchronization.services import create_or_update_contact

                moneybird_contact = create_or_update_contact(moneybird_contact.member)

            contact_id = moneybird_contact.moneybird_id

        invoice_date = date_for_payable_model(self.payable_object).strftime("%Y-%m-%d")

        project_name = project_name_for_payable_model(self.payable_object)

        project_id = None
        if project_name is not None:
            project, __ = MoneybirdProject.objects.get_or_create(name=project_name)
            if project.moneybird_id is None:
                response = moneybird.create_project(project.to_moneybird())
                project.moneybird_id = response["id"]
                project.save()

            project_id = project.moneybird_id

        ledger_id = ledger_id_for_payable_model(self.payable_object)

        period = None
        tax_rate_id = None
        if isinstance(self.payable_object, (Registration, Renewal)):
            period = datetime_to_membership_period(
                self.payable_object.created_at.date()
            )
            tax_rate_id = settings.MONEYBIRD_ZERO_TAX_RATE_ID

        data = {
            "sales_invoice": {
                "contact_id": int(contact_id),
                "reference": f"{self.payable.payment_topic} [{self.payable.model.pk}]",
                "invoice_date": invoice_date,
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

        if project_id is not None:
            data["sales_invoice"]["details_attributes"][0]["project_id"] = int(
                project_id
            )
        if ledger_id is not None:
            data["sales_invoice"]["details_attributes"][0]["ledger_account_id"] = int(
                ledger_id
            )

        if self.moneybird_details_attribute_id is not None:
            data["sales_invoice"]["details_attributes"][0]["id"] = int(
                self.moneybird_details_attribute_id
            )

        if period is not None:
            data["sales_invoice"]["details_attributes"][0]["period"] = period

        if tax_rate_id is not None:
            data["sales_invoice"]["details_attributes"][0]["tax_rate_id"] = int(
                tax_rate_id
            )

        return data

    def __str__(self):
        return f"Moneybird sales invoice for {self.payable_object}"

    class Meta:
        verbose_name = _("moneybird sales invoice")
        verbose_name_plural = _("moneybird sales invoices")
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
            "message": f"{self.payment.pk}; {self.payment.type} by {self.payment.paid_by}; {self.payment.notes}; processed by {self.payment.processed_by or '?'} at {self.payment.created_at:%Y-%m-%d %H:%M:%S}.",
            "amount": str(self.payment.amount),
        }
        if self.moneybird_financial_mutation_id is not None:
            data["financial_mutation_id"] = int(self.moneybird_financial_mutation_id)
            data["financial_account_id"] = financial_account_id_for_payment_type(
                self.payment.type
            )

        return data

    class Meta:
        verbose_name = _("moneybird payment")
        verbose_name_plural = _("moneybird payments")
