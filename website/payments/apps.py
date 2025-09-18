import datetime

from django.apps import AppConfig
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class PaymentsConfig(AppConfig):
    """AppConfig for the payments package."""

    name = "payments"
    verbose_name = _("Payments")

    def user_menu_items(self):
        return {
            "sections": [{"name": "membership", "key": 2}],
            "items": [
                {
                    "section": "membership",
                    "title": "Manage bank account(s)",
                    "url": reverse("payments:bankaccount-list"),
                    "key": 2,
                },
                {
                    "section": "membership",
                    "title": "View payments",
                    "url": reverse("payments:payment-list"),
                    "key": 3,
                },
            ],
        }

    @staticmethod
    def execute_data_minimisation(dry_run=False):
        """Anonymize payments older than 7 years. Also revoke mandates of minimised users."""
        from .models import BankAccount, Payment

        # Sometimes years are 366 days of course, but better delete 1 or 2 days early than late
        payment_deletion_period = timezone.now().date() - timezone.timedelta(
            days=365 * 7
        )
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

        queryset_mandates = BankAccount.objects.filter(
            mandate_no__isnull=False,
            valid_until=None,
            owner__profile__is_minimised=True,
        )

        if not dry_run:
            queryset_payments.update(paid_by=None, processed_by=None)
            queryset_bankaccounts.delete()
            queryset_mandates.update(valid_until=timezone.now())

        return queryset_payments

    @staticmethod
    def minimise_user(user, dry_run: bool = False) -> None:
        from .models import BankAccount, Payment

        queryset_payments = Payment.objects.filter(paid_by=user).exclude(
            paid_by__isnull=True
        )
        queryset_bankaccounts = BankAccount.objects.filter(owner=user)
        queryset_mandates = BankAccount.objects.filter(
            mandate_no__isnull=False,
            valid_until=None,
            owner=user,
        )

        if not dry_run:
            queryset_payments.update(paid_by=None, processed_by=None)
            queryset_bankaccounts.delete()
            queryset_mandates.update(valid_until=timezone.now())

        return (
            queryset_payments.all(),
            queryset_bankaccounts.all(),
            queryset_mandates.all(),
        )
