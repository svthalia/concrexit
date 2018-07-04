from unittest import mock
from unittest.mock import MagicMock, Mock

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.utils import model_ngettext
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.template.defaultfilters import floatformat
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from members.models import Membership
from registrations import views
from registrations.models import Entry, Registration, Renewal
from registrations.views import RenewalFormView


def _get_mock_request(method='GET', is_staff=False,
                      is_authenticated=False, perms=None):
    if perms is None:
        perms = []

    mock_request = HttpRequest()
    mock_request.method = method
    mock_request.META = mock.Mock(return_value={})
    mock_request.user = mock.MagicMock()
    mock_request.user.pk = 1
    mock_request.user.is_staff = is_staff
    mock_request.user.is_authenticated = is_authenticated

    mock_request.user.is_superuser = False
    mock_request.user.user_permissions = perms
    mock_request.user.has_perm = lambda x: x in perms
    mock_request.member = mock_request.user
    mock_request._messages = mock.Mock()
    return mock_request


class EntryAdminViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.entry1 = Registration.objects.create(
            first_name='John',
            last_name='Doe',
            email='johndoe@example.com',
            programme='computingscience',
            student_number='s1234567',
            starting_year=2014,
            address_street='Heyendaalseweg 135',
            address_street2='',
            address_postal_code='6525AJ',
            address_city='Nijmegen',
            phone_number='06123456789',
            birthday=timezone.now().replace(year=1990, day=1),
            language='en',
            length=Entry.MEMBERSHIP_YEAR,
            membership_type=Membership.MEMBER,
            status=Entry.STATUS_CONFIRM,
        )
        cls.user = get_user_model().objects.create_user(username='username')
        cls.entry2 = Renewal.objects.create(
            length=Entry.MEMBERSHIP_YEAR,
            membership_type=Membership.MEMBER,
            status=Entry.STATUS_CONFIRM,
            member=cls.user
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)
        self.view = views.EntryAdminView()

    def _give_user_permissions(self):
        content_type = ContentType.objects.get_for_model(Entry)
        permissions = Permission.objects.filter(
            content_type__app_label=content_type.app_label,
        )
        for p in permissions:
            self.user.user_permissions.add(p)
        self.user.is_staff = True
        self.user.save()

        self.client.logout()
        self.client.force_login(self.user)

    def test_permissions(self):
        url = '/registration/admin/accept/{}/'.format(self.entry1.pk)
        response = self.client.get(url)
        self.assertRedirects(response, '/admin/login/?next=%s' % url)

        self._give_user_permissions()

        url = '/registration/admin/accept/{}/'.format(self.entry1.pk)
        response = self.client.get(url)
        self.assertRedirects(
            response,
            '/admin/registrations/registration/%s/change/' % self.entry1.pk
        )

    @mock.patch('registrations.services.check_unique_user')
    @mock.patch('registrations.services.accept_entries')
    @mock.patch('registrations.services.reject_entries')
    def test_get_accept(self, reject_entries, accept_entries,
                        check_unique_user):
        self.view.action = 'accept'
        for type, entry in {
            'registration': self.entry1,
            'renewal': self.entry2
        }.items():
            entry_qs = Entry.objects.filter(pk=entry.pk)
            check_unique_user.reset_mock()
            check_unique_user.return_value = True
            reject_entries.reset_mock()
            reject_entries.return_value = 1
            accept_entries.reset_mock()
            accept_entries.return_value = 1
            with mock.patch(
                    'registrations.models.Entry.objects.filter') as qs_mock:
                qs_mock.return_value = entry_qs
                qs_mock.get = Mock(return_value=entry_qs.get())

                request = _get_mock_request()
                response = self.view.get(request, pk=entry.pk)

                self.assertEqual(response.status_code, 302)
                self.assertEqual(
                    response.url,
                    '/admin/registrations/%s/%s/change/' % (type, entry.pk)
                )

                accept_entries.assert_called_once_with(entry_qs)
                self.assertFalse(reject_entries.called)

                request._messages.add.assert_called_once_with(
                    messages.SUCCESS, _('Successfully accepted %s.') %
                    model_ngettext(entry_qs.all()[0], 1), '')

                accept_entries.return_value = 0
                self.view.get(request, pk=entry.pk)

                request._messages.add.assert_any_call(
                    messages.ERROR, _('Could not accept %s.') %
                    model_ngettext(entry_qs.all()[0], 1), '')

                accept_entries.return_value = 1
                check_unique_user.return_value = False
                self.view.get(request, pk=entry.pk)

                request._messages.add.assert_any_call(
                    messages.ERROR, _('Could not accept %s. '
                                      'Username is not unique.') %
                    model_ngettext(entry_qs.all()[0], 1), '')

    @mock.patch('registrations.services.accept_entries')
    @mock.patch('registrations.services.reject_entries')
    def test_get_reject(self, reject_entries, accept_entries):
        self.view.action = 'reject'
        for type, entry in {
            'registration': self.entry1,
            'renewal': self.entry2
        }.items():
            accept_entries.reset_mock()
            accept_entries.return_value = 1
            reject_entries.reset_mock()
            reject_entries.return_value = 1
            entry_qs = Entry.objects.filter(pk=entry.pk)
            with mock.patch(
                    'registrations.models.Entry.objects.filter') as qs_mock:
                qs_mock.return_value = entry_qs
                qs_mock.get = Mock(return_value=entry_qs.get())

                request = _get_mock_request()
                response = self.view.get(request, pk=entry.pk)

                self.assertEqual(response.status_code, 302)

                self.assertEqual(
                    response.url,
                    '/admin/registrations/%s/%s/change/' % (type, entry.pk)
                )

                reject_entries.assert_called_once_with(entry_qs)
                self.assertFalse(accept_entries.called)

                request._messages.add.assert_called_once_with(
                    messages.SUCCESS, _('Successfully rejected %s.') %
                    model_ngettext(entry_qs.all()[0], 1), '')

                reject_entries.return_value = 0
                self.view.get(request, pk=entry.pk)

                request._messages.add.assert_any_call(
                    messages.ERROR, _('Could not reject %s.') %
                    model_ngettext(entry_qs.all()[0], 1), '')

    @mock.patch('registrations.models.Entry.objects.filter')
    def test_get_not_exists(self, qs_mock):
        qs_mock.return_value = MagicMock(
            get=Mock(
                side_effect=Entry.DoesNotExist,
                return_value=4,
            )
        )

        request = _get_mock_request()
        response = self.view.get(request, pk=4)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('admin:index'))

    @mock.patch('registrations.services.accept_entries')
    @mock.patch('registrations.services.reject_entries')
    def test_get_no_action(self, reject_entries, accept_entries):
        self.view.action = None
        for type, entry in {
            'registration': self.entry1,
            'renewal': self.entry2
        }.items():
            entry_qs = Entry.objects.filter(pk=entry.pk)
            accept_entries.reset_mock()
            accept_entries.return_value = 1
            reject_entries.reset_mock()
            reject_entries.return_value = 1
            with mock.patch(
                    'registrations.models.Entry.objects.filter') as qs_mock:
                qs_mock.return_value = entry_qs
                qs_mock.get = Mock(return_value=entry_qs.get())

                request = _get_mock_request()
                response = self.view.get(request, pk=entry.pk)

                self.assertFalse(reject_entries.called)
                self.assertFalse(accept_entries.called)

                self.assertEqual(response.status_code, 302)
                self.assertEqual(
                    response.url,
                    '/admin/registrations/%s/%s/change/' % (type, entry.pk)
                )


class ConfirmEmailViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.entry = Registration.objects.create(
            first_name='John',
            last_name='Doe',
            email='johndoe@example.com',
            programme='computingscience',
            student_number='s1234567',
            starting_year=2014,
            address_street='Heyendaalseweg 135',
            address_street2='',
            address_postal_code='6525AJ',
            address_city='Nijmegen',
            phone_number='06123456789',
            birthday=timezone.now().replace(year=1990, day=1),
            language='en',
            length=Entry.MEMBERSHIP_YEAR,
            membership_type=Membership.MEMBER,
            status=Entry.STATUS_CONFIRM,
        )

    def setUp(self):
        self.view = views.ConfirmEmailView()

    @mock.patch('registrations.services.confirm_entry')
    @mock.patch('registrations.emails.send_new_registration_board_message')
    def test_get(self, board_mail, confirm_entry):
        entry_qs = Entry.objects.filter(pk=self.entry.pk)
        with mock.patch(
                'registrations.models.Entry.objects.filter') as qs_mock:
            qs_mock.return_value = entry_qs
            qs_mock.get = Mock(return_value=entry_qs.get())

            request = _get_mock_request()
            self.view.request = request

            response = self.view.get(request, pk=self.entry.pk)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.template_name,
                ['registrations/confirm_email.html']
            )

            confirm_entry.assert_called_once_with(entry_qs)
            board_mail.assert_called_once_with(entry_qs.get())

            confirm_entry.return_value = None

            response = self.view.get(request, pk=self.entry.pk)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, '/registration/register/')

            confirm_entry.side_effect = ValidationError(message='Error')
            board_mail.side_effect = Registration.DoesNotExist

            response = self.view.get(request, pk=self.entry.pk)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, '/registration/register/')

    def test_get_no_mocks(self):
        request = _get_mock_request()
        self.view.request = request

        response = self.view.get(request, pk=self.entry.pk)

        self.assertEqual(response.status_code, 200)


class BecomeAMemberViewTest(TestCase):

    def setUp(self):
        self.view = views.BecomeAMemberView()

    def test_get_context_data(self):
        context = self.view.get_context_data()
        self.assertEqual(len(context), 4)
        self.assertEqual(context['year_fees'], floatformat(
            settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_YEAR], 2))
        self.assertEqual(context['study_fees'], floatformat(
            settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_STUDY], 2))
        self.assertEqual(context['member_form_url'],
                         reverse('registrations:register'))


class MemberRegistrationFormViewTest(TestCase):

    def setUp(self):
        self.view = views.MemberRegistrationFormView()

    def test_get_context_data(self):
        self.view.request = _get_mock_request()
        context = self.view.get_context_data()
        self.assertEqual(len(context), 5)
        self.assertEqual(context['year_fees'], floatformat(
            settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_YEAR], 2))
        self.assertEqual(context['study_fees'], floatformat(
            settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_STUDY], 2))
        self.assertEqual(context['privacy_policy_url'],
                         reverse('privacy-policy'))

    @mock.patch('django.views.generic.FormView.get')
    def test_get(self, super_get):
        super_get.return_value = HttpResponse(status=200)

        request = _get_mock_request(is_authenticated=False)
        response = self.view.get(request)
        self.assertEqual(response.status_code, 200)

        request = _get_mock_request(is_authenticated=True)
        response = self.view.get(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('registrations:renew'))

    @mock.patch('django.views.generic.FormView.post')
    def test_post(self, super_post):
        request = _get_mock_request()
        request.LANGUAGE_CODE = 'nl'
        request.member.pk = 2
        self.view.request = request

        self.view.post(request)

        request = super_post.call_args[0][0]
        self.assertEqual(request.POST['language'], 'nl')
        self.assertEqual(request.POST['membership_type'], Membership.MEMBER)

    def test_form_valid(self):
        mock_form = MagicMock()

        return_value = self.view.form_valid(mock_form)

        mock_form.save.assert_called_once_with()
        self.assertEqual(return_value.status_code, 302)
        self.assertEqual(return_value.url,
                         reverse('registrations:register-success'))


class RenewalFormViewTest(TestCase):

    def setUp(self):
        self.view = views.RenewalFormView()

    def test_get_context_data(self):
        membership = Membership(
            pk=2,
            type=Membership.MEMBER
        )
        self.view.request = MagicMock()

        context = self.view.get_context_data(form=MagicMock())
        self.assertEqual(len(context), 7)
        self.assertEqual(context['year_fees'], floatformat(
            settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_YEAR], 2))
        self.assertEqual(context['study_fees'], floatformat(
            settings.MEMBERSHIP_PRICES[Entry.MEMBERSHIP_STUDY], 2))

        with self.subTest("With latest membership"):
            self.view.request.member.latest_membership = membership

            context = self.view.get_context_data(form=MagicMock())
            self.assertEqual(context['membership'], membership)
            self.assertEqual(context['membership_type'], _('Member'))
            self.assertEqual(context['privacy_policy_url'],
                             reverse('privacy-policy'))

        with self.subTest('Without latest membership'):
            self.view.request.member.latest_membership = None

            context = self.view.get_context_data(form=MagicMock())
            self.assertEqual(context['membership'], None)
            self.assertFalse('membership_type' in context)

    def test_get_form(self):
        self.view.request = _get_mock_request()

        self.view.request.member = None
        form = self.view.get_form()
        self.assertFalse(Entry.MEMBERSHIP_YEAR in
                         form.fields['length'].choices)

        self.view.request.member = MagicMock()
        self.view.request.member.latest_membership = None
        form = self.view.get_form()
        self.assertFalse(Entry.MEMBERSHIP_YEAR in
                         form.fields['length'].choices)

        self.view.request.member.latest_membership = Membership(
            until=None
        )
        form = self.view.get_form()
        self.assertFalse(Entry.MEMBERSHIP_YEAR in
                         form.fields['length'].choices)

        self.view.request.member.latest_membership = Membership(
            until=timezone.now().date()
        )
        form = self.view.get_form()
        self.assertEqual(Entry.MEMBERSHIP_YEAR,
                         form.fields['length'].choices[1][0])

    @mock.patch('django.views.generic.FormView.post')
    def test_post(self, super_post):
        request = _get_mock_request()
        request.member.pk = 2
        self.view.request = request

        self.view.post(request)

        request = super_post.call_args[0][0]
        self.assertEqual(request.POST['member'], 2)
        self.assertEqual(request.POST['membership_type'], Membership.MEMBER)

    @mock.patch('registrations.emails.send_new_renewal_board_message')
    def test_form_valid(self, board_mail):
        mock_form = Mock(spec=RenewalFormView)
        renewal = Renewal(
            pk=2
        )
        mock_form.save = MagicMock(return_value=renewal)

        return_value = self.view.form_valid(mock_form)
        board_mail.assert_called_once_with(renewal)

        self.assertEqual(return_value.status_code, 302)
        self.assertEqual(return_value.url,
                         reverse('registrations:renew-success'))
