"""Tests for things provided by this module"""
import doctest

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings

from activemembers.models import Committee, MemberGroupMembership, Society
from members.models import Profile
from thaliawebsite.templatetags import bleach_tags
from thaliawebsite import sitemaps


def load_tests(_loader, tests, _ignore):
    """
    Load all tests in this module
    """
    # Adds the doctests in bleach_tags
    tests.addTests(doctest.DocTestSuite(bleach_tags))
    tests.addTests(doctest.DocTestSuite(sitemaps))
    return tests


class WikiLoginTestCase(TestCase):
    """Tests event registrations"""
    fixtures = ['member_groups.json']

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username='testuser',
            first_name='first',
            last_name='last_name',
            email='foo@bar.com',
            password='top secret')

    def test_login_get_request_denied(self):
        """GET shouldn't work for the wiki API"""
        response = self.client.get('/api/wikilogin')
        self.assertEqual(response.status_code, 405)

    @override_settings(WIKI_API_KEY='wrongkey')
    def test_login_wrong_apikey(self):
        """API key should be verified"""
        response = self.client.post('/api/wikilogin',
                                    {'apikey': 'rightkey',
                                     'username': 'testuser',
                                     'password': 'top secret'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['status'], 'error')

    @override_settings(WIKI_API_KEY='key')
    def test_login(self):
        """Test a correct log in attempt"""
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
    def test_login_with_profile(self):
        """A user that has a profile should be able to log in"""
        Profile.objects.create(
            user=self.user,
            student_number='s1234567'
        )

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
    def test_login_with_committee_group_membership(self):
        """A user that has a profile should be able to log in"""
        committee = Committee.objects.get(pk=1)
        MemberGroupMembership.objects.create(
            member=self.user,
            group=committee
        )

        response = self.client.post('/api/wikilogin',
                                    {'apikey': 'key',
                                     'user': 'testuser',
                                     'password': 'top secret'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'admin': False,
                                           'committees': ['testcie1:ns'],
                                           'msg': 'Logged in',
                                           'mail': 'foo@bar.com',
                                           'name': 'first last_name',
                                           'status': 'ok'})

    @override_settings(WIKI_API_KEY='key')
    def test_login_with_society_group_membership(self):
        """A user that has a profile should be able to log in"""
        society = Society.objects.get(pk=4)
        MemberGroupMembership.objects.create(
            member=self.user,
            group=society
        )

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
        """The board should get access to the board wiki"""
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
        """Check that the arguments are correct"""
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
        """Check that the password is actually checked"""
        response = self.client.post('/api/wikilogin',
                                    {'apikey': 'key',
                                     'user': 'testuser',
                                     'password': 'wrong secret'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['status'], 'error')
