import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from members.models import Member

from ..models import Reimbursement


class ReimbursementModelTest(TestCase):
    def setUp(self):
        self.user = Member.objects.create_user(username="testuser", password="12345")

    def test_future_date_incurred(self):
        reimbursement = Reimbursement(
            created=timezone.now(),
            date_incurred=timezone.now().date() + datetime.timedelta(days=1),
        )
        with self.assertRaises(ValidationError) as context:
            reimbursement.clean()
        self.assertIn("date_incurred", context.exception.message_dict)
        self.assertEqual(
            context.exception.message_dict["date_incurred"],
            ["The date incurred cannot be in the future."],
        )

    def test_denied_verdict_without_clarification(self):
        reimbursement = Reimbursement(
            created=timezone.now(),
            verdict=Reimbursement.Verdict.DENIED,
        )
        with self.assertRaises(ValidationError) as context:
            reimbursement.clean()
        self.assertIn("verdict_clarification", context.exception.message_dict)
        self.assertEqual(
            context.exception.message_dict["verdict_clarification"],
            ["You must provide a reason for the denial."],
        )

    def test_approved_verdict_without_evaluator(self):
        reimbursement = Reimbursement(
            created=timezone.now(),
            verdict=Reimbursement.Verdict.APPROVED,
        )
        with self.assertRaises(ValidationError) as context:
            reimbursement.clean()
        self.assertIn("evaluated_by", context.exception.message_dict)
        self.assertEqual(
            context.exception.message_dict["evaluated_by"],
            ["You must provide the evaluator."],
        )

    def test_denied_verdict_without_evaluator(self):
        reimbursement = Reimbursement(
            created=timezone.now(),
            verdict=Reimbursement.Verdict.DENIED,
        )
        with self.assertRaises(ValidationError) as context:
            reimbursement.clean()
        self.assertIn("evaluated_by", context.exception.message_dict)
        self.assertEqual(
            context.exception.message_dict["evaluated_by"],
            ["You must provide the evaluator."],
        )

    def test_valid_reimbursement(self):
        reimbursement = Reimbursement(
            created=timezone.now(),
            date_incurred=timezone.now().date(),
            verdict=Reimbursement.Verdict.APPROVED,
            evaluated_by=self.user,
            verdict_clarification="daslkfjlkdsajfkdsajfldsakfjldska",
        )

        reimbursement.clean()
