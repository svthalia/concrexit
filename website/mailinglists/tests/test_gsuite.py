"""Test for the GSuite sync in the mailinglists package"""
from unittest import mock
from unittest.mock import MagicMock

import factory
from django.db.models import signals
from django.test import TestCase
from googleapiclient.errors import HttpError
from googleapiclient.http import HttpMockSequence
from httplib2 import Response

from mailinglists.gsuite import GSuiteSyncService
from mailinglists.models import MailingList, ListAlias, VerbatimAddress


class CatchRequestHttpMockSequence(HttpMockSequence):
    requests = []

    class Request:
        def __init__(self, uri, method, body):
            super().__init__()
            self.uri = uri
            self.method = method
            self.body = body

        def __eq__(self, other: object) -> bool:
            if isinstance(other, self.__class__):
                return self.__dict__ == other.__dict__
            return False

    def request(self, uri, method='GET', body=None, headers=None,
                redirections=1, connection_type=None):
        self.requests.append(self.Request(uri, method, body))
        return super().request(uri, method, body, headers, redirections,
                               connection_type)


# http = CatchRequestHttpMockSequence([
#     ({'status': '200'}, 'data'),
#     ({'status': '200'}, 'data')
# ])


class GSuiteSyncTestCase(TestCase):
    @classmethod
    @factory.django.mute_signals(signals.pre_save)
    def setUpTestData(cls):
        cls.settings_api = MagicMock()
        cls.directory_api = MagicMock()

        cls.sync_service = GSuiteSyncService(
            cls.settings_api, cls.directory_api)
        cls.mailinglist = MailingList.objects.create(
            name='new_group',
            description='some description',
            moderated=False
        )
        ListAlias.objects.create(
            mailinglist=cls.mailinglist, alias='alias2')
        VerbatimAddress.objects.create(
            mailinglist=cls.mailinglist, address='test2@thalia.localhost')

    def setUp(self):
        self.settings_api.reset_mock()
        self.directory_api.reset_mock()

    def test_default_lists(self):
        self.assertEqual(len(self.sync_service._get_default_lists()),
                         18)

    def test_automatic_to_group(self):
        group = GSuiteSyncService._automatic_to_group({
            'moderated': False,
            'name': 'new_group',
            'description': 'some description',
            'aliases': ['alias1'],
            'addresses': ['test1@thalia.localhost']
        })
        self.assertEqual(group, GSuiteSyncService.GroupData(
            'new_group', 'some description', False,
            ['alias1'], ['test1@thalia.localhost']
        ))

    def test_mailinglist_to_group(self):
        group = GSuiteSyncService.mailinglist_to_group(self.mailinglist)
        self.assertEqual(group, GSuiteSyncService.GroupData(
            'new_group', 'some description', False,
            ['alias2'], ['test2@thalia.localhost']
        ))

    def test_group_settings(self):
        self.assertEqual(self.sync_service._group_settings(False), {
            'allowExternalMembers': 'true',
            'allowWebPosting': 'false',
            'archiveOnly': 'false',
            'isArchived': 'true',
            'membersCanPostAsTheGroup': 'false',
            'messageModerationLevel': 'MODERATE_NONE',
            'replyTo': 'REPLY_TO_SENDER',
            'whoCanAssistContent': 'NONE',
            'whoCanContactOwner': 'ALL_MANAGERS_CAN_CONTACT',
            'whoCanDiscoverGroup': 'ALL_MEMBERS_CAN_DISCOVER',
            'whoCanJoin': 'INVITED_CAN_JOIN',
            'whoCanLeaveGroup': 'NONE_CAN_LEAVE',
            'whoCanModerateContent': 'OWNERS_AND_MANAGERS',
            'whoCanModerateMembers': 'NONE',
            'whoCanPostMessage': 'ANYONE_CAN_POST',
            'whoCanViewGroup': 'ALL_MANAGERS_CAN_VIEW',
            'whoCanViewMembership': 'ALL_MANAGERS_CAN_VIEW'
        })
        self.assertEqual(self.sync_service._group_settings(True), {
            'allowExternalMembers': 'true',
            'allowWebPosting': 'false',
            'archiveOnly': 'false',
            'isArchived': 'true',
            'membersCanPostAsTheGroup': 'false',
            'messageModerationLevel': 'MODERATE_ALL_MESSAGES',
            'replyTo': 'REPLY_TO_SENDER',
            'whoCanAssistContent': 'NONE',
            'whoCanContactOwner': 'ALL_MANAGERS_CAN_CONTACT',
            'whoCanDiscoverGroup': 'ALL_MEMBERS_CAN_DISCOVER',
            'whoCanJoin': 'INVITED_CAN_JOIN',
            'whoCanLeaveGroup': 'NONE_CAN_LEAVE',
            'whoCanModerateContent': 'OWNERS_AND_MANAGERS',
            'whoCanModerateMembers': 'NONE',
            'whoCanPostMessage': 'ANYONE_CAN_POST',
            'whoCanViewGroup': 'ALL_MANAGERS_CAN_VIEW',
            'whoCanViewMembership': 'ALL_MANAGERS_CAN_VIEW'
        })

    @mock.patch('mailinglists.gsuite.logger')
    def test_create_group(self, logger_mock):
        with self.subTest('Successful'):
            self.sync_service.create_group(GSuiteSyncService.GroupData(
                'new_group', 'some description', False,
                ['alias2'], ['test2@thalia.localhost']
            ))

            self.directory_api.groups().insert.assert_called_once_with(body={
                'email': 'new_group@thalia.localhost',
                'name': 'new_group',
                'description': 'some description',
            })

            self.settings_api.groups().update.assert_called_once_with(
                groupUniqueId='new_group@thalia.localhost',
                body=self.sync_service._group_settings(False)
            )

            self.directory_api.members().list.assert_called()
            self.directory_api.groups().aliases().list.assert_called()

        self.settings_api.reset_mock()
        self.directory_api.reset_mock()

        with self.subTest('Failure'):
            self.directory_api.groups().insert(body={
                'email': 'new_group@thalia.localhost',
                'name': 'new_group',
                'description': 'some description',
            }).execute.side_effect = HttpError(Response({'status': 500}),
                                               bytes())

            self.sync_service.create_group(GSuiteSyncService.GroupData(
                'new_group', 'some description', False,
                ['alias2'], ['test2@thalia.localhost']
            ))

            self.directory_api.members().list.assert_not_called()
            self.directory_api.groups().aliases().list.assert_not_called()

            logger_mock.error.assert_called_once_with(
                'Could not successfully finish '
                'creating the list new_group', bytes()
            )


