from django.apps import AppConfig
from django.utils import timezone

from members.models import Member

from .models.order import Order


class SalesConfig(AppConfig):
    name = "sales"

    def ready(self):
        from .payables import register

        register()

    def execute_data_minimisation(self, dry_run=False):
        """Anonymizes orders older than 3 years."""
        # Sometimes years are 366 days of course, but better delete 1 or 2 days early than late

        deletion_period = timezone.now().date() - timezone.timedelta(days=365 * 3)

        queryset = Order.objects.filter(created_at__lte=deletion_period).exclude(
            payer__isnull=True
        )
        if not dry_run:
            queryset.update(payer=None)
        return queryset.all()

    def minimize_user(self, user: Member, dry_run: bool = False) -> None:
        queryset = Order.objects.filter(payer=user)
        if not dry_run:
            queryset.update(payer=None)
        return queryset.all()
