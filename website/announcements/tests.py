from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase, RequestFactory
from django.urls import reverse

from announcements.views import close_announcement


class AnnouncementCloseTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='thom',
            email='test@example.com',
            password='top secret',
        )
        self.middleware = SessionMiddleware()

    def test_get_request(self):
        for user in [self.user, AnonymousUser()]:
            request = self.factory.get(
                reverse('announcements:close-announcement'))
            self.middleware.process_request(request)
            with self.subTest(user=user):
                request.user = user
                response = close_announcement(request)
                self.assertEqual(response.status_code, 405)

    def test_post_no_id(self):
        request = self.factory.post(
            reverse('announcements:close-announcement'))
        self.middleware.process_request(request)
        request.user = AnonymousUser()
        response = close_announcement(request)
        self.assertEqual(response.status_code, 400)

    def test_post_id_string(self):
        request = self.factory.post(
            reverse('announcements:close-announcement'),
            {'id': 'bla'})
        self.middleware.process_request(request)
        request.user = AnonymousUser()
        response = close_announcement(request)
        self.assertEqual(response.status_code, 400)

    def test_valid_request_anonymous(self):
        request = self.factory.post(
            reverse('announcements:close-announcement'),
            {'id': 3})
        self.middleware.process_request(request)
        request.user = AnonymousUser()
        response = close_announcement(request)

        self.assertEqual(response.status_code, 204)
        self.assertIn('closed_announcements', request.session)
        self.assertIn(3, request.session['closed_announcements'])
        self.assertTrue(request.session.modified)
        self.assertEqual(response.content, b'')

    def test_valid_request_logged_in(self):
        request = self.factory.post(
            reverse('announcements:close-announcement'),
            {'id': 3})
        self.middleware.process_request(request)
        request.user = self.user
        response = close_announcement(request)

        self.assertEqual(response.status_code, 204)
        self.assertIn('closed_announcements', request.session)
        self.assertIn(3, request.session['closed_announcements'])
        self.assertEqual(response.content, b'')
