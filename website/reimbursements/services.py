import logging
from datetime import timedelta

from django.utils import timezone

from .models import Reimbursement

logger = logging.getLogger(__name__)
YEAR = timedelta(days=365)


def execute_data_minimisation(dry_run=False):
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
    _delete_old_reimbursements(Reimbursement.Verdict.APPROVED, years_until_deletion=7)
