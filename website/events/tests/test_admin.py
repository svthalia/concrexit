import datetime
from unittest import mock

from django.contrib.admin import AdminSite
from django.http import HttpResponseRedirect
from django.test import TestCase, RequestFactory
from django.utils import timezone

from activemembers.models import Committee, CommitteeMembership
from events.admin import DoNextModelAdmin, RegistrationInformationFieldInline
from events.models import Event, RegistrationInformationField
from members.models import Member


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


class RegistrationInformationFieldInlineTest(TestCase):
    fixtures = ['members.json', 'committees.json']

    @classmethod
    def setUpTestData(cls):
        cls.committee = Committee.objects.get(pk=1)
        cls.event = Event.objects.create(
            pk=1,
            organiser=cls.committee,
            title_nl='testevenement',
            title_en='testevent',
            description_en='desc',
            description_nl='besch',
            published=True,
            start=(timezone.now() + datetime.timedelta(hours=1)),
            end=(timezone.now() + datetime.timedelta(hours=2)),
            location_en='test location',
            location_nl='test locatie',
            map_location='test map location',
            price=0.00,
            fine=0.00)
        cls.member = Member.objects.filter(last_name="Wiggers").first()
        cls.member.is_superuser = True
        cls.member.save()
        CommitteeMembership.objects.create(
            member=cls.member,
            committee=cls.committee
        )

        RegistrationInformationField.objects.create(
            pk=1,
            event=cls.event,
            type=RegistrationInformationField.BOOLEAN_FIELD,
            name_en="test bool",
            name_nl="test bool",
            required=False
        )

        RegistrationInformationField.objects.create(
            pk=2,
            event=cls.event,
            type=RegistrationInformationField.INTEGER_FIELD,
            name_en="test int",
            name_nl="test int",
            required=False
        )

        RegistrationInformationField.objects.create(
            pk=3,
            event=cls.event,
            type=RegistrationInformationField.TEXT_FIELD,
            name_en="test text",
            name_nl="test text",
            required=False
        )

    def setUp(self):
        self.site = AdminSite()
        self.inline = RegistrationInformationFieldInline(Event,
                                                         self.site)
        self.rf = RequestFactory()

    def test_get_formset(self):
        request = self.rf.get('/admin/events/event/1/change/')
        request.user = self.member

        formset = self.inline.get_formset(request, None)
        self.assertEqual(0, formset.form.declared_fields['order'].initial)

        formset = self.inline.get_formset(request, self.event)
        self.assertEqual(3, formset.form.declared_fields['order'].initial)


class EventAdminTest(TestCase):

    def setUp(self):
        pass
