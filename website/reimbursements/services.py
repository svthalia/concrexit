import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import Reimbursement

logger = logging.getLogger(__name__)

def execute_data_minimisation(dry_run=False):
    def _delete_old_reimbursements(
        verdict: Reimbursement.Verdict,
        days_until_deletion: int,
    ):
        old_reimbursements = Reimbursement.objects.filter(
            verdict=verdict,
            created__lt=timezone.now() - days_until_deletion,
        )

        logger.info(
            "Deleting %d %s reimbursements", old_reimbursements.count(), verdict
        )
        if not dry_run:
            old_reimbursements.delete()

    _delete_old_reimbursements(Reimbursement.Verdict.DENIED, 
        days_until_deletion=settings.DATA_RETENTION_PERIODS["REIMBURSEMENTS_DENIED"]
    )

    _delete_old_reimbursements(Reimbursement.Verdict.APPROVED, 
        days_until_deletion=settings.DATA_RETENTION_PERIODS["REIMBURSEMENTS_APPROVED"]
    )
