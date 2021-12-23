"""The services defined by the payments package."""
import datetime
from typing import Union

from django.conf import settings
from django.core import mail
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet, Q, Sum, Model
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from members.models import Member
from utils.snippets import send_email

from .exceptions import PaymentError
from .models import BankAccount, Payment, PaymentUser
from .payables import Payable, payables, NotRegistered
from .signals import processed_batch


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
    if pay_type not in (Payment.CASH, Payment.CARD, Payment.WIRE, Payment.TPAY):
        raise PaymentError("Invalid payment type")

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

    if not payable.paying_allowed:
        raise PaymentError(_("Payment restricted"))

    if payable.payment is not None:
        payable.payment.amount = payable.payment_amount
        payable.payment.notes = payable.payment_notes
        payable.payment.topic = payable.payment_topic
        payable.payment.paid_by = payer
        payable.payment.processed_by = processed_by
        payable.payment.type = pay_type
        payable.payment.payable_model = (
            ContentType.objects.get_for_model(payable.model),
        )
        payable.payment.payable_object_id = payable.model.pk
        payable.payment.save()
        LogEntry.objects.log_action(
            user_id=processed_by.id,
            content_type_id=ContentType.objects.get_for_model(Payment).pk,
            object_id=payable.payment.id,
            object_repr=str(payable.payment),
            action_flag=CHANGE,
        )
    else:
        payable.payment = Payment.objects.create(
            processed_by=processed_by,
            amount=payable.payment_amount,
            notes=payable.payment_notes,
            topic=payable.payment_topic,
            paid_by=payer,
            type=pay_type,
            payable_model=ContentType.objects.get_for_model(payable.model),
            payable_object_id=payable.model.pk,
        )
        LogEntry.objects.log_action(
            user_id=processed_by.id,
            content_type_id=ContentType.objects.get_for_model(Payment).pk,
            object_id=payable.payment.id,
            object_repr=str(payable.payment),
            action_flag=ADDITION,
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
    now = timezone.now()
    if not date:
        date = now.date()

    result = queryset.filter(
        Q(valid_from__gte=now, valid_until__lt=now) | Q(valid_until=None)
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
        if not bank_account:  # pragma: no cover
            # This should not happen, cannot happen, does not happen (right... ;p)
            # but if it does, we don't want to crash, but just remove the payment from the batch (make it unprocessed)
            payment.batch = None
            payment.save()
        else:
            bank_account.last_used = batch.withdrawal_date
            bank_account.save(update_fields=["last_used"])

    batch.save()
    processed_batch.send(sender=None, instance=batch)

    send_tpay_batch_processing_emails(batch)


def derive_next_mandate_no(member) -> str:
    accounts = (
        BankAccount.objects.filter(owner=PaymentUser.objects.get(pk=member.pk))
        .exclude(mandate_no=None)
        .filter(mandate_no__regex=BankAccount.MANDATE_NO_DEFAULT_REGEX)
    )
    new_mandate_no = 1 + max(
        (int(account.mandate_no.split("-")[1]) for account in accounts), default=0
    )
    return f"{member.pk}-{new_mandate_no}"


def send_tpay_batch_processing_emails(batch):
    """Send withdrawal notice emails to all members in a batch."""
    member_payments = batch.payments_set.values("paid_by").annotate(total=Sum("amount"))
    with mail.get_connection() as connection:
        for member_row in member_payments:
            member = PaymentUser.objects.get(pk=member_row["paid_by"])
            total_amount = member_row["total"]

            send_email(
                to=[member.email],
                subject="Thalia Pay withdrawal notice",
                txt_template="payments/email/tpay_withdrawal_notice_mail.txt",
                html_template="payments/email/tpay_withdrawal_notice_mail.html",
                connection=connection,
                context={
                    "name": member.get_full_name(),
                    "batch": batch,
                    "bank_account": member.bank_accounts.filter(
                        mandate_no__isnull=False
                    ).last(),
                    "creditor_id": settings.SEPA_CREDITOR_ID,
                    "payments": batch.payments_set.filter(paid_by=member),
                    "total_amount": total_amount,
                    "payments_url": (
                        settings.BASE_URL
                        + reverse(
                            "payments:payment-list",
                        )
                    ),
                },
            )
    return len(member_payments)


def execute_data_minimisation(dry_run=False):
    """Anonymizes payments older than 7 years."""
    # Sometimes years are 366 days of course, but better delete 1 or 2 days early than late
    payment_deletion_period = timezone.now().date() - timezone.timedelta(days=365 * 7)
    bankaccount_deletion_period = timezone.now() - datetime.timedelta(days=31 * 13)

    queryset_payments = Payment.objects.filter(
        created_at__lte=payment_deletion_period
    ).exclude(paid_by__isnull=True)

    # Delete bank accounts that are not valid anymore, and have not been used in the last 13 months
    # (13 months is the required time we need to keep the mandates for)
    queryset_bankaccounts = BankAccount.objects.all()
    queryset_bankaccounts = queryset_bankaccounts.filter(
        valid_until__lt=timezone.now()
    )  # We must always keep valid bank accounts. so we only select the ones that are not valid anymore (valid_until < now)
    queryset_bankaccounts = queryset_bankaccounts.exclude(  # Also keep bank accounts that
        Q(
            owner__paid_payment_set__type=Payment.TPAY
        ),  # are used for Thalia Pay payments, AND
        Q(
            owner__paid_payment_set__batch__isnull=True
        )  # have a payment that is in no batch, OR
        | Q(
            owner__paid_payment_set__batch__processed=False
        )  # have an unprocessed batch, OR
        | Q(
            owner__paid_payment_set__batch__processing_date__gt=bankaccount_deletion_period  # or have a processed batch that is not older than 13 months
        ),
    )

    if not dry_run:
        queryset_payments.update(paid_by=None, processed_by=None)
        queryset_bankaccounts.delete()
    return queryset_payments


def get_payable_content_types():
    results = []
    for content_type in ContentType.objects.all():
        try:
            payables.get_payable(content_type.model_class())
        except NotRegistered:
            pass
        else:
            results.append(content_type.id)
    return ContentType.objects.filter(id__in=results)
