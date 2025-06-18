from django.conf import settings

from celery import shared_task

from moneybirdsynchronization import services
from reimbursements.models import Reimbursement


@shared_task
def synchronize_moneybird():
    if not settings.MONEYBIRD_SYNC_ENABLED:
        return

    services.synchronize_moneybird()


@shared_task
def synchronize_moneybird_reimbursement(reimbursement_id):
    """Push the receipt for an approved reimbursement to Moneybird immediately.

    This happens at night automatically, but can be triggered individually to
    allow the treasurer to continue working quickly.
    """
    if not settings.MONEYBIRD_SYNC_ENABLED:
        return

    reimbursement = Reimbursement.objects.get(
        id=reimbursement_id, verdict=Reimbursement.Verdict.APPROVED
    )

    owner = reimbursement.owner
    if (
        not hasattr(owner, "moneybird_contact")
        or owner.moneybird_contact.needs_synchronization
    ):
        services.create_or_update_contact(owner)

    services.create_receipt(reimbursement)
