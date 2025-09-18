from django.apps import AppConfig
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class PizzasConfig(AppConfig):
    """AppConfig for the pizzas package."""

    name = "pizzas"
    verbose_name = _("Pizzas")

    def ready(self):
        from .payables import register

        register()

    @staticmethod
    def execute_data_minimisation(dry_run=False):
        """Anonymizes pizzas orders older than 3 years."""
        # Sometimes years are 366 days of course, but better delete 1 or 2 days early than late
        from .models import FoodOrder

        deletion_period = timezone.now().date() - timezone.timedelta(days=365 * 3)

        queryset = FoodOrder.objects.filter(
            food_event__end__lte=deletion_period
        ).exclude(name="<removed>")
        if not dry_run:
            queryset.update(member=None, name="<removed>")
        return queryset

    @staticmethod
    def minimise_user(user, dry_run=False) -> None:
        from .models import FoodOrder

        queryset = FoodOrder.objects.filter(member=user)
        if not dry_run:
            queryset.update(member=None, name="<removed>")
        return queryset
