"""The services defined by the payments package"""
import datetime
from typing import Union

from django.conf import settings
from django.db.models import QuerySet, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from members.models import Member
from .exceptions import PaymentError
from .models import Payment, BankAccount, Payable


def create_payment(
    payable: Payable,
    processed_by: Member,
    pay_type: Union[Payment.CASH, Payment.CARD, Payment.WIRE, Payment.TPAY],
) -> Payment:
    """
    Create a new payment from a payable object

    :param payable: Payable object
    :param processed_by: Member that processed this payment
    :param pay_type: Payment type
    :return: Payment object
    """
    if pay_type == Payment.TPAY and not payable.payment_payer.tpay_enabled:
        raise PaymentError(_("This user does not have Thalia Pay enabled"))

    if payable.payment is not None:
        payable.payment.amount = payable.payment_amount
        payable.payment.notes = payable.payment_notes
        payable.payment.topic = payable.payment_topic
        payable.payment.paid_by = payable.payment_payer
        payable.payment.processed_by = processed_by
        payable.payment.type = pay_type
        payable.payment.save()
    else:
        payable.payment = Payment.objects.create(
            processed_by=processed_by,
            amount=payable.payment_amount,
            notes=payable.payment_notes,
            topic=payable.payment_topic,
            paid_by=payable.payment_payer,
            type=pay_type,
        )
    return payable.payment


def delete_payment(payable: Payable):
    """
    Removes a payment from a payable object
    :param payable: Payable object
    :return:
    """
    payment = payable.payment
    if payment.created_at < timezone.now() - timezone.timedelta(
        seconds=settings.PAYMENT_CHANGE_WINDOW
    ):
        raise PaymentError(_("You are not authorized to delete this payment."))

    payable.payment = None
    payable.save()
    payment.delete()


def update_last_used(queryset: QuerySet, date: datetime.date = None) -> int:
    """
    Update the last used field of a BankAccount queryset

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
    """
    Revokes all mandates that have not been used for 36 months or more
    :return: number of affected rows
    """
    return BankAccount.objects.filter(
        last_used__lte=(timezone.now() - timezone.timedelta(days=36 * 30))
    ).update(valid_until=timezone.now().date())
