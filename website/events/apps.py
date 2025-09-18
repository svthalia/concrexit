from django.apps import AppConfig
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class EventsConfig(AppConfig):
    """AppConfig for the events package."""

    name = "events"
    verbose_name = _("Events")

    def ready(self):
        from . import signals  # noqa: F401
        from .payables import register

        register()

    def menu_items(self):
        return {
            "categories": [{"name": "association", "title": "Association", "key": 1}],
            "items": [
                {
                    "category": "association",
                    "title": "Alumni",
                    "url": reverse("events:alumni"),
                    "key": 7,
                },
                {
                    "title": "Calendar",
                    "url": reverse("events:index"),
                    "key": 3,
                },
            ],
        }

    @staticmethod
    def execute_data_minimisation(dry_run=False):
        """Delete information about very old events."""
        # Sometimes years are 366 days of course, but better delete 1 or 2 days early than late
        from .models.event_registration import EventRegistration

        deletion_period = timezone.now().date() - timezone.timedelta(days=365 * 5)

        queryset = EventRegistration.objects.filter(
            event__end__lte=deletion_period
        ).filter(
            Q(payment__isnull=False)
            | Q(member__isnull=False)
            | ~Q(name__exact="<removed>")
        )
        if not dry_run:
            queryset.update(payment=None, member=None, name="<removed>")
        return queryset.all()

    @staticmethod
    def minimise_user(user, dry_run=False) -> None:
        from .models.event_registration import EventRegistration

        queryset = EventRegistration.objects.filter(
            Q(payment__isnull=False) | Q(date__lte=timezone.now()), member=user
        )
        if not dry_run:
            queryset.update(payment=None, member=None, name="<removed>")
        return queryset.all()
