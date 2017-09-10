import doctest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings

from thaliawebsite.templatetags import bleach_tags


def load_tests(loader, tests, ignore):
    """
    Load all tests in this module
    """
    # Adds the doctests in bleach_tags
    tests.addTests(doctest.DocTestSuite(bleach_tags))
    return tests


class WikiLoginTestCase(TestCase):
    """Tests event registrations"""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username='testuser',
            first_name='first',
            last_name='last_name',
            email='foo@bar.com',
            password='top secret')

    def test_login_GET_denied(self):
        response = self.client.get('/api/wikilogin')
        self.assertEqual(response.status_code, 405)

    @override_settings(WIKI_API_KEY='wrongkey')
    def test_login_wrong_apikey(self):
        response = self.client.post('/api/wikilogin',
                                    {'apikey': 'rightkey',
                                     'username': 'testuser',
                                     'password': 'top secret'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['status'], 'error')

    @override_settings(WIKI_API_KEY='key')
    def test_login(self):
        response = self.client.post('/api/wikilogin',
                                    {'apikey': 'key',
                                     'user': 'testuser',
                                     'password': 'top secret'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'admin': False,
                                           'committees': [],
                                           'msg': 'Logged in',
                                           'mail': 'foo@bar.com',
                                           'name': 'first last_name',
                                           'status': 'ok'})

    @override_settings(WIKI_API_KEY='key')
    def test_board_permission(self):
        self.user.user_permissions.add(
            Permission.objects.get(codename='board_wiki'))
        response = self.client.post('/api/wikilogin',
                                    {'apikey': 'key',
                                     'user': 'testuser',
                                     'password': 'top secret'})
        self.assertEqual(response.json(), {'admin': False,
                                           'committees': ['bestuur'],
                                           'msg': 'Logged in',
                                           'mail': 'foo@bar.com',
                                           'name': 'first last_name',
                                           'status': 'ok'})
        self.assertEqual(response.status_code, 200)

    @override_settings(WIKI_API_KEY='key')
    def test_wrongargs(self):
        response = self.client.post('/api/wikilogin',
                                    {'apikey': 'key',
                                     'username': 'testuser',
                                     'password': 'top secret'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

        response = self.client.post('/api/wikilogin',
                                    {'apikey': 'key',
                                     'user': 'testuser'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')

    @override_settings(WIKI_API_KEY='key')
    def test_login_wrong_password(self):
        response = self.client.post('/api/wikilogin',
                                    {'apikey': 'key',
                                     'user': 'testuser',
                                     'password': 'wrong secret'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['status'], 'error')
