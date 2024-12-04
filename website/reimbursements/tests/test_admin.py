from django.contrib.admin.sites import AdminSite
from django.test import TestCase
from django.utils import timezone

from members.models import Member
from reimbursements.admin import ReimbursementsAdmin
from reimbursements.models import Reimbursement


class MockRequest:
    def __init__(self, user):
        self.user = user


class ReimbursementsAdminTests(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.user = Member.objects.create_user(username="testuser", password="12345")
        self.superuser = Member.objects.create_superuser(
            username="admin", password="12345", email="admin@example.com"
        )
        self.reimbursement = Reimbursement.objects.create(
            owner=self.user,
            description="Test reimbursement",
            amount=100,
            date_incurred=timezone.now(),
        )
        self.admin = ReimbursementsAdmin(model=Reimbursement, admin_site=self.site)

    def test_get_queryset_for_superuser(self):
        request = MockRequest(self.superuser)
        queryset = self.admin.get_queryset(request)
        self.assertIn(self.reimbursement, queryset)

    def test_get_queryset_for_normal_user(self):
        request = MockRequest(self.user)
        queryset = self.admin.get_queryset(request)
        self.assertIn(self.reimbursement, queryset)

    def test_save_model_sets_owner(self):
        request = MockRequest(self.superuser)
        reimbursement = Reimbursement(
            description="Another test", amount=200, date_incurred=timezone.now()
        )
        self.admin.save_model(request, reimbursement, None, False)
        self.assertEqual(reimbursement.owner, self.superuser)

    def test_get_readonly_fields(self):
        self.reimbursement.verdict = "approved"
        self.reimbursement.verdict_clarification = "Approved by admin"
        request = MockRequest(self.superuser)
        readonly_fields = self.admin.get_readonly_fields(request, self.reimbursement)
        self.assertIn("description", readonly_fields)
        self.assertIn("amount", readonly_fields)
        self.assertIn("date_incurred", readonly_fields)
        self.assertIn("receipt", readonly_fields)
        self.assertIn("verdict", readonly_fields)
        self.assertIn("verdict_clarification", readonly_fields)

    def test_has_view_permission(self):
        request = MockRequest(self.user)
        request.member = self.user
        self.assertTrue(self.admin.has_view_permission(request, self.reimbursement))
        request.user = self.superuser
        self.assertTrue(self.admin.has_view_permission(request, self.reimbursement))
