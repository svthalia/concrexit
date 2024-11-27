from datetime import timedelta

from django.utils import timezone

from .models import Reimbursement

# TODO: remove DECLINED reimburstments after two years since verdict_date
#       remove APPROVED reimburstments after seven years since the verdict_date


YEAR = timedelta(days=365)


def execute_data_minimisation(dry_run=False):
    declined_reimburstments = Reimbursement.objects.filter(
        verdict=Reimbursement.Verdict.DENIED
    )

    for reimbursement in declined_reimburstments:
        if reimbursement.created.date() + YEAR * 2 < timezone.now().date():
            reimbursement.delete()

    approved_reimbursements = Reimbursement.objects.filter(
        verdict=Reimbursement.Verdict.APPROVED
    )

    for reimbursement in approved_reimbursements:
        if reimbursement.created.date() + YEAR * 7 < timezone.now().date():
            reimbursement.delete()
