from unittest import mock

from django.contrib.admin import AdminSite
from django.http import HttpResponseRedirect
from django.test import TestCase, RequestFactory

from events.admin import DoNextModelAdmin
from events.models import Event


class DoNextModelAdminTest(TestCase):

    def setUp(self):
        self.site = AdminSite()
        self.admin = DoNextModelAdmin(Event, admin_site=self.site)
        self.rf = RequestFactory()

    @mock.patch('utils.translation.TranslatedModelAdmin.response_add')
    def test_response_add(self, super_mock):
        super_mock.return_value = None

        request = self.rf.get('/admin/events/event/1')
        response = self.admin.response_add(request, None)
        self.assertIsNone(response, HttpResponseRedirect)

        request = self.rf.get('/admin/events/event/1', data={
            'next': 'http://example.org',
        })
        response = self.admin.response_add(request, None)
        self.assertIsNone(response, HttpResponseRedirect)

        request = self.rf.get('/admin/events/event/1', data={
            'next': '/test',
        })
        response = self.admin.response_add(request, None)
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual('/test', response.url)

    @mock.patch('utils.translation.TranslatedModelAdmin.response_change')
    def test_response_change(self, super_mock):
        super_mock.return_value = None

        request = self.rf.get('/admin/events/event/1')
        response = self.admin.response_change(request, None)
        self.assertIsNone(response, HttpResponseRedirect)

        request = self.rf.get('/admin/events/event/1', data={
            'next': 'http://example.org',
        })
        response = self.admin.response_change(request, None)
        self.assertIsNone(response, HttpResponseRedirect)

        request = self.rf.get('/admin/events/event/1', data={
            'next': '/test',
        })
        response = self.admin.response_change(request, None)
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual('/test', response.url)
