"""The services defined by the payments package."""
import datetime
from typing import Union

from django.conf import settings
from django.db.models import QuerySet, Q, Sum, Model
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from members.models import Member
from utils.snippets import send_email
from .exceptions import PaymentError
from .models import Payment, BankAccount, PaymentUser
from .payables import payables, Payable


def create_payment(
    model_payable: Union[Model, Payable],
    processed_by: Member,
    pay_type: Union[Payment.CASH, Payment.CARD, Payment.WIRE, Payment.TPAY],
) -> Payment:
    """Create a new payment from a payable object.

    :param model_payable: Payable or Model object
    :param processed_by: PaymentUser that processed this payment
    :param pay_type: Payment type
    :return: Payment object
    """
    if isinstance(model_payable, Payable):
        payable = model_payable
    else:
        payable = payables.get_payable(model_payable)

    payer = (
        PaymentUser.objects.get(pk=payable.payment_payer.pk)
        if payable.payment_payer
        else None
    )

    if not (
        (payer and payer == processed_by and pay_type == Payment.TPAY)
        or (payable.can_manage_payment(processed_by) and pay_type != Payment.TPAY)
    ):
        raise PaymentError(
            _("User processing payment does not have the right permissions")
        )

    if payable.payment_amount == 0:
        raise PaymentError(_("Payment amount 0 is not accepted"))

    if pay_type == Payment.TPAY and not payer.tpay_enabled:
        raise PaymentError(_("This user does not have Thalia Pay enabled"))

    if payable.payment is not None:
        payable.payment.amount = payable.payment_amount
        payable.payment.notes = payable.payment_notes
        payable.payment.topic = payable.payment_topic
        payable.payment.paid_by = payer
        payable.payment.processed_by = processed_by
        payable.payment.type = pay_type
        payable.payment.save()
    else:
        payable.payment = Payment.objects.create(
            processed_by=processed_by,
            amount=payable.payment_amount,
            notes=payable.payment_notes,
            topic=payable.payment_topic,
            paid_by=payer,
            type=pay_type,
        )
    return payable.payment


def delete_payment(model: Model, member: Member = None, ignore_change_window=False):
    """Remove a payment from a payable object.

    :param model: Payable or Model object
    :param member: member deleting the payment
    :param ignore_change_window: ignore the payment change window
    :return:
    """
    payable = payables.get_payable(model)

    if member and not payable.can_manage_payment(member):
        raise PaymentError(
            _("User deleting payment does not have the right permissions.")
        )

    payment = payable.payment
    if (
        payment.created_at
        < timezone.now() - timezone.timedelta(seconds=settings.PAYMENT_CHANGE_WINDOW)
        and not ignore_change_window
    ):
        raise PaymentError(_("This payment cannot be deleted anymore."))
    if payment.batch and payment.batch.processed:
        raise PaymentError(
            _("This payment has already been processed and hence cannot be deleted.")
        )

    payable.payment = None
    payable.model.save()
    payment.delete()


def update_last_used(queryset: QuerySet, date: datetime.date = None) -> int:
    """Update the last used field of a BankAccount queryset.

    :param queryset: Queryset of BankAccounts
    :param date: date to set last_used to
    :return: number of affected rows
    """
    if not date:
        date = timezone.now().date()

    result = queryset.filter(
        (Q(valid_from__gte=timezone.now()) & Q(valid_until__lt=timezone.now()))
        | Q(valid_until=None)
    ).update(last_used=date)
    return result


def revoke_old_mandates() -> int:
    """Revoke all mandates that have not been used for 36 months or more.

    :return: number of affected rows
    """
    return BankAccount.objects.filter(
        last_used__lte=(timezone.now() - timezone.timedelta(days=36 * 30))
    ).update(valid_until=timezone.now().date())


def process_batch(batch):
    """Process a Thalia Pay batch.

    :param batch: the batch to be processed
    :return:
    """
    batch.processed = True

    payments = batch.payments_set.select_related("paid_by")
    for payment in payments:
        bank_account = payment.paid_by.bank_accounts.last()
        bank_account.last_used = batch.withdrawal_date
        bank_account.save()

    batch.save()

    send_tpay_batch_processing_emails(batch)


def derive_next_mandate_no(member) -> str:
    accounts = (
        BankAccount.objects.filter(owner=PaymentUser.objects.get(pk=member.pk))
        .exclude(mandate_no=None)
        .filter(mandate_no__regex=BankAccount.MANDATE_NO_DEFAULT_REGEX)
    )
    new_mandate_no = 1 + max(
        [int(account.mandate_no.split("-")[1]) for account in accounts], default=0
    )
    return f"{member.pk}-{new_mandate_no}"


def send_tpay_batch_processing_emails(batch):
    """Send withdrawal notice emails to all members in a batch."""
    member_payments = batch.payments_set.values("paid_by").annotate(total=Sum("amount"))
    for member_row in member_payments:
        member = PaymentUser.objects.get(pk=member_row["paid_by"])
        total_amount = member_row["total"]

        send_email(
            member.email,
            _("Thalia Pay withdrawal notice"),
            "payments/email/tpay_withdrawal_notice_mail.txt",
            {
                "name": member.get_full_name(),
                "batch": batch,
                "bank_account": member.bank_accounts.filter(
                    mandate_no__isnull=False
                ).last(),
                "creditor_id": settings.SEPA_CREDITOR_ID,
                "payments": batch.payments_set.filter(paid_by=member),
                "total_amount": total_amount,
                "payments_url": (settings.BASE_URL + reverse("payments:payment-list",)),
            },
        )
    return len(member_payments)
