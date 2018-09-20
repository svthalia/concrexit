from unittest import mock
from unittest.mock import Mock

from django.contrib import messages
from django.contrib.admin import AdminSite
from django.contrib.admin.utils import model_ngettext
from django.http import HttpRequest
from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from members.models import Member
from payments.models import Payment
from registrations import admin
from registrations.models import Entry, Registration, Renewal


def _get_mock_request(perms=None):
    if perms is None:
        perms = []

    mock_request = HttpRequest()
    mock_request.META = mock.Mock(return_value={})
    mock_request.user = mock.MagicMock()
    mock_request.user.is_superuser = False
    mock_request.user.user_permissions = perms
    mock_request.user.has_perm = lambda x: x in perms
    mock_request._messages = mock.Mock()
    return mock_request


class GlobalAdminTest(SimpleTestCase):

    @mock.patch('registrations.admin.RegistrationAdmin')
    def test_show_message(self, admin_mock):
        admin_mock.return_value = admin_mock
        request = Mock(spec=HttpRequest)

        admin._show_message(admin_mock, request, 0, 'message', 'error')
        admin_mock.message_user.assert_called_once_with(
            request, 'error', messages.ERROR)
        admin_mock.message_user.reset_mock()
        admin._show_message(admin_mock, request, 1, 'message', 'error')
        admin_mock.message_user.assert_called_once_with(
            request, 'message', messages.SUCCESS)


class RegistrationAdminTest(TestCase):
    fixtures = ['members.json']

    def setUp(self):
        self.site = AdminSite()
        self.admin = admin.RegistrationAdmin(Registration,
                                             admin_site=self.site)

    @mock.patch('django.contrib.admin.ModelAdmin.changeform_view')
    @mock.patch('registrations.models.Entry.objects.get')
    def test_changeform_view(self, entry_get, super_method):
        request = _get_mock_request()
        object_id = None
        form_url = 'form://url'

        registration = Registration.objects.create(
            status=Entry.STATUS_REVIEW,
            birthday=timezone.now()
        )
        entry = registration.entry_ptr
        entry_get.return_value = entry

        self.admin.changeform_view(request, object_id, form_url)
        self.assertFalse(entry_get.called)
        super_method.assert_called_once_with(request, object_id, form_url, {
            'entry': None,
            'can_review': False,
            'can_resend': False,
        })

        super_method.reset_mock()
        entry_get.reset_mock()
        request = _get_mock_request(perms=['registrations.review_entries'])

        self.admin.changeform_view(request, object_id, form_url)
        self.assertFalse(entry_get.called)
        super_method.assert_called_once_with(request, object_id, form_url, {
            'entry': None,
            'can_review': False,
            'can_resend': False,
        })

        super_method.reset_mock()
        entry_get.reset_mock()
        object_id = entry.pk

        self.admin.changeform_view(request, object_id, form_url)
        self.assertTrue(entry_get.called)
        super_method.assert_called_once_with(request, object_id, form_url, {
            'entry': entry,
            'can_review': True,
            'can_resend': False,
        })

        super_method.reset_mock()
        entry_get.reset_mock()
        registration.status = Entry.STATUS_CONFIRM
        registration.save()
        entry = registration.entry_ptr
        entry_get.return_value = entry

        self.admin.changeform_view(request, object_id, form_url)
        self.assertTrue(entry_get.called)
        super_method.assert_called_once_with(request, object_id, form_url, {
            'entry': entry,
            'can_review': False,
            'can_resend': True,
        })

        super_method.reset_mock()
        entry_get.reset_mock()
        registration.status = Entry.STATUS_ACCEPTED
        registration.save()
        entry = registration.entry_ptr
        entry_get.return_value = entry

        self.admin.changeform_view(request, object_id, form_url)
        self.assertTrue(entry_get.called)
        super_method.assert_called_once_with(request, object_id, form_url, {
            'entry': entry,
            'can_review': False,
            'can_resend': False,
        })

        super_method.reset_mock()
        renewal = Renewal.objects.create(
            status=Entry.STATUS_REVIEW,
            member=Member.objects.filter(last_name="Wiggers").first()
        )
        entry = renewal.entry_ptr
        entry_get.return_value = entry
        object_id = entry.pk

        self.admin.changeform_view(request, object_id, form_url)
        self.assertTrue(entry_get.called)
        super_method.assert_called_once_with(request, object_id, form_url, {
            'entry': entry,
            'can_review': True,
            'can_resend': False,
        })

    @mock.patch('registrations.services.accept_entries')
    def test_accept(self, accept_entries):
        accept_entries.return_value = 1

        queryset = []

        request = _get_mock_request([])

        self.admin.accept_selected(request, queryset)
        accept_entries.assert_not_called()

        request = _get_mock_request(['registrations.review_entries'])
        self.admin.accept_selected(request, queryset)

        accept_entries.assert_called_once_with(queryset)

        request._messages.add.assert_called_once_with(
            messages.SUCCESS,
            _('Successfully accepted %(count)d %(items)s.')
            % {
                "count": 1,
                "items": model_ngettext(Registration(), 1)
            }, '')

    @mock.patch('registrations.services.reject_entries')
    def test_reject(self, reject_entries):
        reject_entries.return_value = 1

        queryset = []

        request = _get_mock_request([])

        self.admin.reject_selected(request, queryset)
        reject_entries.assert_not_called()

        request = _get_mock_request(['registrations.review_entries'])
        self.admin.reject_selected(request, queryset)
        reject_entries.assert_called_once_with(queryset)

        request._messages.add.assert_called_once_with(
            messages.SUCCESS,
            _('Successfully rejected %(count)d %(items)s.')
            % {
                "count": 1,
                "items": model_ngettext(Registration(), 1)
            }, '')

    def test_get_readonly_fields(self):
        request = _get_mock_request([])

        fields = self.admin.get_readonly_fields(request)
        self.assertEqual(fields, ['status', 'created_at',
                                  'updated_at'])

        fields = self.admin.get_readonly_fields(request, Registration(
            status=Entry.STATUS_CONFIRM
        ))
        self.assertEqual(fields, ['status', 'created_at',
                                  'updated_at'])

        fields = self.admin.get_readonly_fields(request, Registration(
            status=Entry.STATUS_REJECTED
        ))
        self.assertCountEqual(fields, ['created_at', 'updated_at', 'status',
                                       'length', 'membership_type', 'remarks',
                                       'entry_ptr', 'username',
                                       'first_name', 'last_name',
                                       'birthday', 'language', 'email',
                                       'phone_number', 'student_number',
                                       'programme', 'starting_year',
                                       'address_street', 'address_street2',
                                       'address_postal_code', 'address_city',
                                       'membership', 'optin_mailinglist',
                                       'optin_birthday'])

        fields = self.admin.get_readonly_fields(request, Registration(
            status=Entry.STATUS_ACCEPTED
        ))
        self.assertCountEqual(fields, ['created_at', 'updated_at', 'status',
                                       'length', 'membership_type', 'remarks',
                                       'entry_ptr', 'username',
                                       'first_name', 'last_name',
                                       'birthday', 'language', 'email',
                                       'phone_number', 'student_number',
                                       'programme', 'starting_year',
                                       'address_street', 'address_street2',
                                       'address_postal_code', 'address_city',
                                       'membership', 'optin_mailinglist',
                                       'optin_birthday'])

        fields = self.admin.get_readonly_fields(request, Registration(
            status=Entry.STATUS_COMPLETED
        ))
        self.assertCountEqual(fields, ['created_at', 'updated_at', 'status',
                                       'length', 'membership_type', 'remarks',
                                       'entry_ptr', 'username',
                                       'first_name', 'last_name',
                                       'birthday', 'language', 'email',
                                       'phone_number', 'student_number',
                                       'programme', 'starting_year',
                                       'address_street', 'address_street2',
                                       'address_postal_code', 'address_city',
                                       'membership', 'optin_mailinglist',
                                       'optin_birthday'])

    def test_get_actions(self):
        actions = self.admin.get_actions(_get_mock_request([]))
        self.assertCountEqual(actions, ['delete_selected'])

        actions = self.admin.get_actions(
            _get_mock_request(['registrations.review_entries']))
        self.assertCountEqual(actions, ['delete_selected', 'accept_selected',
                                        'reject_selected'])

    def test_name(self):
        reg = Registration(
            first_name='John',
            last_name='Doe',
        )
        self.assertEqual(self.admin.name(reg), reg.get_full_name())

    def test_payment_status(self):
        reg = Registration(
            username='johnnytest',
            payment=Payment(
                pk='123',
                processed=False
            )
        )

        self.assertEqual(
            self.admin.payment_status(reg),
            '<a href="{}">{}</a>'.format(
                '/admin/payments/payment/123/change/',
                _('Unprocessed')))

        reg.payment.processed = True

        self.assertEqual(
            self.admin.payment_status(reg),
            '<a href="{}">{}</a>'.format(
                '/admin/payments/payment/123/change/',
                _('Processed')))

        reg.payment = None
        self.assertEqual(self.admin.payment_status(reg), '-')


class RenewalAdminTest(TestCase):

    def setUp(self):
        self.site = AdminSite()
        self.admin = admin.RenewalAdmin(Renewal, admin_site=self.site)

    @mock.patch('registrations.services.accept_entries')
    def test_accept(self, accept_entries):
        accept_entries.return_value = 1

        queryset = []

        request = _get_mock_request([])

        self.admin.accept_selected(request, queryset)
        accept_entries.assert_not_called()

        request = _get_mock_request(['registrations.review_entries'])
        self.admin.accept_selected(request, queryset)

        accept_entries.assert_called_once_with(queryset)

        request._messages.add.assert_called_once_with(
            messages.SUCCESS,
            _('Successfully accepted %(count)d %(items)s.')
            % {
                "count": 1,
                "items": model_ngettext(Renewal(), 1)
            }, '')

    @mock.patch('registrations.services.reject_entries')
    def test_reject(self, reject_entries):
        reject_entries.return_value = 1

        queryset = []

        request = _get_mock_request([])

        self.admin.reject_selected(request, queryset)
        reject_entries.assert_not_called()

        request = _get_mock_request(['registrations.review_entries'])
        self.admin.reject_selected(request, queryset)
        reject_entries.assert_called_once_with(queryset)

        request._messages.add.assert_called_once_with(
            messages.SUCCESS,
            _('Successfully rejected %(count)d %(items)s.')
            % {
                "count": 1,
                "items": model_ngettext(Renewal(), 1)
            }, '')

    def test_get_readonly_fields(self):
        request = _get_mock_request([])

        fields = self.admin.get_readonly_fields(request)
        self.assertEqual(fields, ['status', 'created_at',
                                  'updated_at'])

        fields = self.admin.get_readonly_fields(request, Renewal(
            status=Entry.STATUS_CONFIRM
        ))
        self.assertEqual(fields, ['status', 'created_at',
                                  'updated_at', 'member'])

        fields = self.admin.get_readonly_fields(request, Renewal(
            status=Entry.STATUS_REJECTED
        ))
        self.assertCountEqual(fields, ['created_at', 'updated_at', 'status',
                                       'length', 'membership_type', 'remarks',
                                       'entry_ptr', 'member',
                                       'membership'])

        fields = self.admin.get_readonly_fields(request, Renewal(
            status=Entry.STATUS_ACCEPTED
        ))
        self.assertCountEqual(fields, ['created_at', 'updated_at', 'status',
                                       'length', 'membership_type', 'remarks',
                                       'entry_ptr', 'member',
                                       'membership'])

    def test_get_actions(self):
        actions = self.admin.get_actions(_get_mock_request([]))
        self.assertCountEqual(actions, ['delete_selected'])

        actions = self.admin.get_actions(
            _get_mock_request(['registrations.review_entries']))
        self.assertCountEqual(actions, ['delete_selected', 'accept_selected',
                                        'reject_selected'])

    def test_name(self):
        renewal = Renewal(
            member=Member(
                first_name='John',
                last_name="Doe",
            )
        )
        self.assertEqual(self.admin.name(renewal),
                         renewal.member.get_full_name())

    def test_email(self):
        renewal = Renewal(
            member=Member(
                email='test@example.org'
            )
        )
        self.assertEqual(self.admin.email(renewal),
                         'test@example.org')
