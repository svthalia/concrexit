from django.apps import AppConfig
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from members.models import Member

from .models import FoodOrder


class PizzasConfig(AppConfig):
    """AppConfig for the pizzas package."""

    name = "pizzas"
    verbose_name = _("Pizzas")

    def ready(self):
        from .payables import register

        register()

    def execute_data_minimisation(self, dry_run=False):
        """Anonymizes pizzas orders older than 3 years."""
        # Sometimes years are 366 days of course, but better delete 1 or 2 days early than late

        deletion_period = timezone.now().date() - timezone.timedelta(days=365 * 3)

        queryset = FoodOrder.objects.filter(
            food_event__end__lte=deletion_period
        ).exclude(name="<removed>")
        if not dry_run:
            queryset.update(member=None, name="<removed>")
        return queryset

    def minimize_user(self, user: Member, dry_run: bool = False) -> None:
        queryset = FoodOrder.objects.filter(member=user)
        if not dry_run:
            queryset.update(member=None, name="<removed>")
        return queryset
