import logging
from datetime import timedelta

from django.apps import AppConfig
from django.utils import timezone

from members.models.member import Member

from .models import Reimbursement

logger = logging.getLogger(__name__)
YEAR = timedelta(days=365)


class ReimbursementsConfig(AppConfig):
    name = "reimbursements"
    verbose_name = "Reimbursements"

    def execute_data_minimisation(self, dry_run=False):
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

    def minimize_user(self, user: Member, dry_run: bool = False) -> None:
        queryset = Reimbursement.objects.filter(member=user).exclude(verdict=None)
        if not dry_run:
            queryset.update(member=None)
        return queryset.all()
