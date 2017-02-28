from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings

from members.models import Member
from thaliapp.models import Token


class RaaSTestCase(SimpleTestCase):

    def test_raas(self):
        response = self.client.get('/api/randomasaservice')
        self.assertEqual(response.json()['status'], 'ok')
        self.assertIn('random', response.json())
        response = self.client.post('/api/randomasaservice')
        self.assertEqual(response.json()['status'], 'ok')
        self.assertIn('random', response.json())


# preimage: key
@override_settings(
    THALIAPP_API_KEY=('2c70e12b7a0646f92279f427c7b38e'
                      '7334d8e5389cff167a1dc30e73f826b683'))
class AppApiTestCase(TestCase):
    """Tests event registrations"""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username='testuser',
            first_name='first',
            last_name='last_name',
            email='foo@bar.com',
            password='top secret')
        cls.member = Member.objects.create(
            user=cls.user,
            birthday=datetime(1993, 3, 2)
        )

        cls.token = Token.create_token(cls.user)

    def test_GET_denied(self):
        response = self.client.get('/api/login')
        self.assertEqual(response.status_code, 405)
        response = self.client.get('/api/app')
        self.assertEqual(response.status_code, 405)

    def test_wrong_apikey(self):
        response = self.client.post('/api/login',
                                    {'apikey': 'bla',
                                     'username': 'testuser',
                                     'password': 'top secret'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['status'], "error")

        response = self.client.post('/api/app',
                                    {'apikey': 'bla',
                                     'username': 'testuser',
                                     'token': self.token})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['status'], "error")

    def test_wrong_arguments(self):
        response = self.client.post('/api/login',
                                    {'apikey': 'key',
                                     'username': 'testuser',
                                     'pas': 'top secret'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], "error")
        response = self.client.post('/api/login',
                                    {'apikey': 'key',
                                     'user': 'testuser',
                                     'password': 'top secret'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], "error")

        response = self.client.post('/api/app',
                                    {'apikey': 'key',
                                     'username': 'testuser',
                                     'tok': self.token})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], "error")
        response = self.client.post('/api/login',
                                    {'apikey': 'key',
                                     'user': 'testuser',
                                     'token': self.token})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], "error")

    def test_wrong_password(self):
        response = self.client.post('/api/login',
                                    {'apikey': 'key',
                                     'username': 'testuser',
                                     'password': 'wrong'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['status'], "error")

    def test_correct_login(self):
        response = self.client.post('/api/login',
                                    {'apikey': 'key',
                                     'username': 'testuser',
                                     'password': 'top secret'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')
        self.assertEqual(response.json()['username'], 'testuser')
        self.assertIn('token', response.json())
        self.assertIn('profile_image', response.json())

    def test_correct_token_login(self):
        response = self.client.post('/api/app',
                                    {'apikey': 'key',
                                     'username': 'testuser',
                                     'token': self.token})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('profile_image', data)
        del data['profile_image']
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['birthday'], '1993-03-02')
        self.assertEqual(data['real_name'], 'first last_name')
        self.assertEqual(data['display_name'], 'first last_name')
        self.assertEqual(data['membership_type'], 'Expired')
        self.assertEqual(data['over18'], True)
        self.assertEqual(data['is_thalia_member'], False)
