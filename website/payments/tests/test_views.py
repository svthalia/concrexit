from unittest import mock
from unittest.mock import Mock

from django.contrib.admin.utils import model_ngettext
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import Client, TestCase
from django.utils.translation import ugettext_lazy as _

from payments import views
from payments.models import Payment


class PaymentAdminViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.payment = Payment.objects.create(
            processed=False,
            amount=7.5
        )
        cls.user = get_user_model().objects.create_user(username='username')

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)
        self.view = views.PaymentAdminView()

    def _give_user_permissions(self):
        content_type = ContentType.objects.get_for_model(Payment)
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
        url = '/payment/admin/process/{}/'.format(
            self.payment.pk)
        response = self.client.post(url, {
            'type': 'cash_payment',
        })
        self.assertRedirects(response, '/admin/login/?next=%s' % url)

        self._give_user_permissions()

        url = '/payment/admin/process/{}/'.format(
            self.payment.pk)
        response = self.client.post(url, {
            'type': 'cash_payment',
        })
        self.assertRedirects(
            response,
            '/admin/payments/payment/%s/change/' % self.payment.pk
        )

    @mock.patch('django.contrib.messages.error')
    @mock.patch('django.contrib.messages.success')
    @mock.patch('payments.services.process_payment')
    def test_post(self, process_payment, messages_success, messages_error):
        process_payment.return_value = [self.payment]
        payment_qs = Payment.objects.filter(pk=self.payment.pk)

        with mock.patch('payments.models.Payment.objects.filter') as qs_mock:
            qs_mock.return_value = payment_qs
            qs_mock.get = Mock(return_value=payment_qs)

            self._give_user_permissions()

            with self.subTest('Send post without payload'):
                response = self.client.post('/payment/admin/process/{}/'
                                            .format(self.payment.pk))

                self.assertEqual(response.status_code, 302)
                self.assertEqual(
                    response.url,
                    '/admin/payments/payment/%s/change/' % self.payment.pk
                )

                process_payment.assert_not_called()
                messages_error.assert_not_called()
                messages_success.assert_not_called()

            with self.subTest('Send post with successful processing'):
                payment_type = 'cash_payment'
                response = self.client.post('/payment/admin/process/{}/'
                                            .format(self.payment.pk), {
                                                'type': payment_type,
                                            })

                self.assertEqual(response.status_code, 302)
                self.assertEqual(
                    response.url,
                    '/admin/payments/payment/%s/change/' % self.payment.pk
                )

                process_payment.assert_called_once_with(payment_qs, payment_type)

                messages_success.assert_called_once_with(
                    response.wsgi_request, _('Successfully processed %s.') %
                                           model_ngettext(self.payment, 1)
                )

            with self.subTest('Send post with failed processing'):
                process_payment.return_value = []
                response = self.client.post('/payment/admin/process/{}/'
                                            .format(self.payment.pk), {
                                                'type': payment_type,
                                            })

                messages_error.assert_called_once_with(
                    response.wsgi_request, _('Could not process %s.') %
                                           model_ngettext(self.payment, 1)
                )
