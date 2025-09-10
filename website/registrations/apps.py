from django.apps import AppConfig
from django.db.models import Q, Value
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class RegistrationsConfig(AppConfig):
    """AppConfig for the registrations package."""

    name = "registrations"
    verbose_name = _("Registrations")

    def ready(self):
        """Import the signals when the app is ready."""
        from . import signals  # noqa: F401
        from .payables import register

        register()

    def menu_items(self):
        return {
            "categories": [{"name": "association", "title": "Association", "key": 1}],
            "items": [
                {
                    "category": "association",
                    "title": "Become a member",
                    "url": reverse("registrations:index"),
                    "key": 6,
                },
            ],
        }

    def user_menu_items(self):
        return {
            "sections": [{"name": "membership", "key": 2}],
            "items": [
                {
                    "section": "membership",
                    "title": "Manage membership",
                    "url": reverse("registrations:renew"),
                    "key": 1,
                },
            ],
        }

    @staticmethod
    def execute_data_minimisation(dry_run=False):
        """Delete completed or rejected registrations that were modified at least 31 days ago.

        :param dry_run: does not really remove data if True
        :return: number of removed objects.
        """
        from .models import Entry, Registration, Renewal

        deletion_period = timezone.now() - timezone.timedelta(days=31)
        registrations = Registration.objects.filter(
            Q(status=Entry.STATUS_COMPLETED) | Q(status=Entry.STATUS_REJECTED),
            updated_at__lt=deletion_period,
        )
        renewals = Renewal.objects.filter(
            Q(status=Entry.STATUS_COMPLETED) | Q(status=Entry.STATUS_REJECTED),
            updated_at__lt=deletion_period,
        )

        if dry_run:
            return registrations.count() + renewals.count()  # pragma: no cover

        # Mark that this deletion is for data minimisation so that it can be recognized
        # in any post_delete signal handlers. This is used to prevent the deletion of
        # Moneybird invoices.
        registrations = registrations.annotate(
            __deleting_for_dataminimisation=Value(True)
        )
        renewals = renewals.annotate(__deleting_for_dataminimisation=Value(True))

        return registrations.delete()[0] + renewals.delete()[0]

    @staticmethod
    def minimize_user(user, dry_run: bool = False) -> None:
        from .models import Entry, Registration, Renewal

        registrations = Registration.objects.filter(
            Q(status=Entry.STATUS_COMPLETED) | Q(status=Entry.STATUS_REJECTED),
            member=user,
        )
        renewals = Renewal.objects.filter(
            Q(status=Entry.STATUS_COMPLETED) | Q(status=Entry.STATUS_REJECTED),
            member=user,
        )
        if not dry_run:
            registrations.update(member=None)
            renewals.update(member=None)
        return registrations.all(), renewals.all()
