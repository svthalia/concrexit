from unittest import mock
from unittest.mock import Mock

from django.contrib import messages
from django.contrib.admin import AdminSite
from django.contrib.admin.utils import model_ngettext
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.http import HttpRequest
from django.test import TestCase, SimpleTestCase, Client, RequestFactory
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from payments import admin
from payments.models import Payment


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


class PaymentAdminTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username='username',
            is_staff=True,
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)
        self.factory = RequestFactory()
        self.site = AdminSite()
        self.admin = admin.PaymentAdmin(Payment, admin_site=self.site)

        self._give_user_permissions()
        process_perm = Permission.objects.get(
            content_type__model='payment',
            codename='process_payments')
        self.user.user_permissions.remove(process_perm)
        self.client.logout()
        self.client.force_login(self.user)

    def _give_user_permissions(self):
        content_type = ContentType.objects.get_for_model(Payment)
        permissions = Permission.objects.filter(
            content_type__app_label=content_type.app_label,
        )
        for p in permissions:
            self.user.user_permissions.add(p)
        self.user.save()

        self.client.logout()
        self.client.force_login(self.user)

    @mock.patch('payments.models.Payment.objects.get')
    def test_changeform_view(self, payment_get):
        object_id = 'c85ea333-3508-46f1-8cbb-254f8c138020'
        payment = Payment.objects.create(pk=object_id,
                                         processed=False,
                                         amount=7.5)
        payment_get.return_value = payment

        response = self.client.get('/admin/payments/payment/add/')
        self.assertFalse(payment_get.called)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['payment'], None)
        response = self.client.get('/admin/payments/payment/{}/change/'
                                   .format(object_id), follow=True)
        self.assertFalse(payment_get.called)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['payment'], None)

        self._give_user_permissions()

        response = self.client.get('/admin/payments/payment/{}/change/'
                                   .format(object_id))
        self.assertTrue(payment_get.called)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['payment'], payment)

        payment.processed = True

        response = self.client.get('/admin/payments/payment/{}/change/'
                                   .format(object_id))
        self.assertTrue(payment_get.called)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['payment'], None)

    @mock.patch('django.contrib.admin.ModelAdmin.message_user')
    @mock.patch('payments.services.process_payment')
    def test_process_cash(self, process_payment, message_user):
        object_id = 'c85ea333-3508-46f1-8cbb-254f8c138020'
        payment = Payment.objects.create(pk=object_id,
                                         processed=False,
                                         amount=7.5)
        queryset = Payment.objects.filter(pk=object_id)
        process_payment.return_value = [payment]
        change_url = reverse('admin:payments_payment_changelist')

        request_noperms = self.client.post(
            change_url,
            {'action': 'process_cash_selected',
             'index': 1,
             '_selected_action': [object_id]}).wsgi_request
        self._give_user_permissions()
        request_hasperms = self.client.post(
            change_url,
            {'action': 'process_cash_selected',
             'index': 1,
             '_selected_action': [object_id]}).wsgi_request

        process_payment.reset_mock()
        message_user.reset_mock()

        self.admin.process_cash_selected(request_noperms, queryset)
        process_payment.assert_not_called()

        self.admin.process_cash_selected(request_hasperms, queryset)
        process_payment.assert_called_once_with(queryset, Payment.CASH)
        message_user.assert_called_once_with(
            request_hasperms,
            _('Successfully processed %(count)d %(items)s.')
            % {
                "count": 1,
                "items": model_ngettext(Payment(), 1)
            }, messages.SUCCESS
        )

    @mock.patch('django.contrib.admin.ModelAdmin.message_user')
    @mock.patch('payments.services.process_payment')
    def test_process_card(self, process_payment, message_user):
        object_id = 'c85ea333-3508-46f1-8cbb-254f8c138020'
        payment = Payment.objects.create(pk=object_id,
                                         processed=False,
                                         amount=7.5)
        queryset = Payment.objects.filter(pk=object_id)
        process_payment.return_value = [payment]
        change_url = reverse('admin:payments_payment_changelist')

        request_noperms = self.client.post(
            change_url,
            {'action': 'process_card_selected',
             'index': 1,
             '_selected_action': [object_id]}).wsgi_request
        self._give_user_permissions()
        request_hasperms = self.client.post(
            change_url,
            {'action': 'process_card_selected',
             'index': 1,
             '_selected_action': [object_id]}).wsgi_request

        process_payment.reset_mock()
        message_user.reset_mock()

        self.admin.process_card_selected(request_noperms, queryset)
        process_payment.assert_not_called()

        self.admin.process_card_selected(request_hasperms, queryset)
        process_payment.assert_called_once_with(queryset, Payment.CARD)
        message_user.assert_called_once_with(
            request_hasperms,
            _('Successfully processed %(count)d %(items)s.')
            % {
                "count": 1,
                "items": model_ngettext(Payment(), 1)
            }, messages.SUCCESS
        )

    def test_get_actions(self):
        response = self.client.get(
            reverse('admin:payments_payment_changelist'))

        actions = self.admin.get_actions(response.wsgi_request)
        self.assertCountEqual(actions, ['delete_selected'])

        self._give_user_permissions()
        response = self.client.get(
            reverse('admin:payments_payment_changelist'))

        actions = self.admin.get_actions(response.wsgi_request)
        self.assertCountEqual(actions, ['delete_selected',
                                        'process_cash_selected',
                                        'process_card_selected'])
