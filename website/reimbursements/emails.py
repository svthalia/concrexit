from reimbursements.models import Reimbursement
from utils.snippets import send_email


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
