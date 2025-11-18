from django.apps import AppConfig
from django.utils import timezone


class SalesConfig(AppConfig):
    name = "sales"

    def ready(self):
        from .payables import register

        register()

    @staticmethod
    def execute_data_minimisation(dry_run=False):
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

    @staticmethod
    def minimise_user(user, dry_run: bool = False) -> None:
        from .models.order import Order

        queryset = Order.objects.filter(payer=user)
        if not dry_run:
            queryset.update(payer=None)
        if dry_run:
            return queryset.all()
