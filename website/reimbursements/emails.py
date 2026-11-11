from reimbursements.models import Reimbursement
from utils.snippets import send_email


def send_new_reimbursement_email(reimbursement: Reimbursement):
    send_email(
        to=["treasurer@thalia.nu"],
        subject="New Reimbursement has appeared",
        txt_template="reimbursements/email/new_reimbursement.txt",
        html_template="reimbursements/email/new_reimbursement.html",
        context={
            "first_name": reimbursement.owner.first_name,
            "description": reimbursement.description,
            "amount": reimbursement.amount,
        },
    )


def send_verdict_email(reimbursement: Reimbursement):
    send_email(
        to=[reimbursement.owner.email],
        subject="Reimbursement request",
        txt_template="reimbursements/email/verdict.txt",
        html_template="reimbursements/email/verdict.html",
        context={
            "first_name": reimbursement.owner.first_name,
            "description": reimbursement.description,
            "verdict": reimbursement.verdict,
            "verdict_clarification": reimbursement.verdict_clarification,
        },
    )
