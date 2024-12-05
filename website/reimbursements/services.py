import logging
from datetime import timedelta

from django.utils import timezone

from .models import Reimbursement

logger = logging.getLogger(__name__)
YEAR = timedelta(days=365)


def execute_data_minimisation(dry_run=False):
    old_declined_reimbursements = Reimbursement.objects.filter(
        verdict=Reimbursement.Verdict.DENIED,
        created__lt=timezone.now() - YEAR * 2,
    )

    logger.info(
        "Deleting %d declined reimbursements", old_declined_reimbursements.count()
    )
    if not dry_run:
        old_declined_reimbursements.delete()

    old_approved_reimbursements = Reimbursement.objects.filter(
        verdict=Reimbursement.Verdict.APPROVED,
        created__lt=timezone.now() - YEAR * 7,
    )

    logger.info(
        "Deleting %d approved reimbursements", old_approved_reimbursements.count()
    )
    if not dry_run:
        old_approved_reimbursements.delete()
