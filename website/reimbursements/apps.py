import logging
from datetime import timedelta

from django.apps import AppConfig
from django.utils import timezone

from thaliawebsite.apps import MinimisationError

logger = logging.getLogger(__name__)
YEAR = timedelta(days=365)


class ReimbursementsConfig(AppConfig):
    name = "reimbursements"
    verbose_name = "Reimbursements"

    @staticmethod
    def execute_data_minimisation(dry_run=False):
        from .models import Reimbursement

        def _delete_old_reimbursements(
            verdict: Reimbursement.Verdict,
            years_until_deletion: int,
        ):
            old_reimbursements = Reimbursement.objects.filter(
                verdict=verdict,
                created__lt=timezone.now() - YEAR * years_until_deletion,
            )

            logger.info(
                "Deleting %d %s reimbursements", old_reimbursements.count(), verdict
            )
            if not dry_run:
                old_reimbursements.delete()

        _delete_old_reimbursements(Reimbursement.Verdict.DENIED, years_until_deletion=2)
        _delete_old_reimbursements(
            Reimbursement.Verdict.APPROVED, years_until_deletion=7
        )

    @staticmethod
    def minimise_user(user, dry_run: bool = False) -> None:
        from .models import Reimbursement

        queryset = Reimbursement.objects.filter(owner=user)
        month_verdict = queryset.filter(
            evaluated_at__gt=timezone.now() - timedelta.days(31),
            verdict=Reimbursement.Verdict.APPROVED,
        )

        if month_verdict:
            raise MinimisationError(
                "A reimbursement exists that should is approved too shortly ago exists."
            )
        open_reimbursements = queryset.filter(verdict=None)

        if open_reimbursements.exists():
            raise MinimisationError("Cannot minimise user with open reimbursements.")

        if not dry_run:
            queryset.update(member=None)
        return queryset.all()
