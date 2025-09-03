from django.apps import AppConfig
from django.utils import timezone


class SalesConfig(AppConfig):
    name = "sales"

    def ready(self):
        from .payables import register

        register()

    def execute_data_minimisation(self, dry_run=False):
        """Anonymizes orders older than 3 years."""
        # Sometimes years are 366 days of course, but better delete 1 or 2 days early than late
        from .models.order import Order

        deletion_period = timezone.now().date() - timezone.timedelta(days=365 * 3)

        queryset = Order.objects.filter(created_at__lte=deletion_period).exclude(
            payer__isnull=True
        )
        if not dry_run:
            queryset.update(payer=None)
        return queryset.all()

    def minimize_user(self, user, dry_run: bool = False) -> None:
        from .models.order import Order

        queryset = Order.objects.filter(payer=user)
        if not dry_run:
            queryset.update(payer=None)
        return queryset.all()
