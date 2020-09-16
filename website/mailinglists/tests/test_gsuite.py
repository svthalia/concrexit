"""Test for the GSuite sync in the mailinglists package"""
from unittest import mock
from unittest.mock import MagicMock

from django.conf import settings
from django.test import TestCase, override_settings
from googleapiclient.errors import HttpError
from httplib2 import Response

from mailinglists.gsuite import GSuiteSyncService
from mailinglists.models import MailingList, ListAlias, VerbatimAddress


def assert_not_called_with(self, *args, **kwargs):
    try:
        self.assert_any_call(*args, **kwargs)
    except AssertionError:
        return
    raise AssertionError(
        "Expected %s to not have been called."
        % self._format_mock_call_signature(args, kwargs)
    )


MagicMock.assert_not_called_with = assert_not_called_with


@override_settings(SUSPEND_SIGNALS=True)
class GSuiteSyncTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.settings_api = MagicMock()
        cls.directory_api = MagicMock()

        cls.sync_service = GSuiteSyncService(cls.settings_api, cls.directory_api)
        cls.mailinglist = MailingList.objects.create(
            name="new_group", description="some description", moderated=False
        )
        ListAlias.objects.create(mailinglist=cls.mailinglist, alias="alias2")
        VerbatimAddress.objects.create(
            mailinglist=cls.mailinglist, address=f"test2@{settings.GSUITE_DOMAIN}"
        )

    def setUp(self):
        self.settings_api.reset_mock()
        self.directory_api.reset_mock()

    def test_default_lists(self):
        self.assertEqual(len(self.sync_service._get_default_lists()), 13)

    def test_automatic_to_group(self):
        group = GSuiteSyncService._automatic_to_group(
            {
                "moderated": False,
                "name": "new_group",
                "description": "some description",
                "aliases": ["alias1"],
                "addresses": [f"test1@{settings.GSUITE_DOMAIN}"],
            }
        )
        self.assertEqual(
            group,
            GSuiteSyncService.GroupData(
                "new_group",
                "some description",
                False,
                ["alias1"],
                [f"test1@{settings.GSUITE_DOMAIN}"],
            ),
        )

    def test_mailinglist_to_group(self):
        group = GSuiteSyncService.mailinglist_to_group(self.mailinglist)
        self.assertEqual(
            group,
            GSuiteSyncService.GroupData(
                "new_group",
                "some description",
                False,
                ["alias2"],
                [f"test2@{settings.GSUITE_DOMAIN}"],
            ),
        )

    def test_group_settings(self):
        self.assertEqual(
            self.sync_service._group_settings(False),
            {
                "allowExternalMembers": "true",
                "allowWebPosting": "false",
                "archiveOnly": "false",
                "isArchived": "true",
                "membersCanPostAsTheGroup": "false",
                "messageModerationLevel": "MODERATE_NONE",
                "replyTo": "REPLY_TO_SENDER",
                "whoCanAssistContent": "NONE",
                "whoCanContactOwner": "ALL_MANAGERS_CAN_CONTACT",
                "whoCanDiscoverGroup": "ALL_MEMBERS_CAN_DISCOVER",
                "whoCanJoin": "INVITED_CAN_JOIN",
                "whoCanLeaveGroup": "NONE_CAN_LEAVE",
                "whoCanModerateContent": "OWNERS_AND_MANAGERS",
                "whoCanModerateMembers": "NONE",
                "whoCanPostMessage": "ANYONE_CAN_POST",
                "whoCanViewGroup": "ALL_MEMBERS_CAN_VIEW",
                "whoCanViewMembership": "ALL_MANAGERS_CAN_VIEW",
            },
        )
        self.assertEqual(
            self.sync_service._group_settings(True),
            {
                "allowExternalMembers": "true",
                "allowWebPosting": "false",
                "archiveOnly": "false",
                "isArchived": "true",
                "membersCanPostAsTheGroup": "false",
                "messageModerationLevel": "MODERATE_ALL_MESSAGES",
                "replyTo": "REPLY_TO_SENDER",
                "whoCanAssistContent": "NONE",
                "whoCanContactOwner": "ALL_MANAGERS_CAN_CONTACT",
                "whoCanDiscoverGroup": "ALL_MEMBERS_CAN_DISCOVER",
                "whoCanJoin": "INVITED_CAN_JOIN",
                "whoCanLeaveGroup": "NONE_CAN_LEAVE",
                "whoCanModerateContent": "OWNERS_AND_MANAGERS",
                "whoCanModerateMembers": "NONE",
                "whoCanPostMessage": "ANYONE_CAN_POST",
                "whoCanViewGroup": "ALL_MEMBERS_CAN_VIEW",
                "whoCanViewMembership": "ALL_MANAGERS_CAN_VIEW",
            },
        )

    @mock.patch("mailinglists.gsuite.logger")
    def test_create_group(self, logger_mock):
        with self.subTest("Successful"):
            self.sync_service.create_group(
                GSuiteSyncService.GroupData(
                    "new_group",
                    "some description",
                    False,
                    ["alias2"],
                    [f"test2@{settings.GSUITE_DOMAIN}"],
                )
            )

            self.directory_api.groups().insert.assert_called_once_with(
                body={
                    "email": f"new_group@{settings.GSUITE_DOMAIN}",
                    "name": "new_group",
                    "description": "some description",
                }
            )

            self.settings_api.groups().update.assert_called_once_with(
                groupUniqueId=f"new_group@{settings.GSUITE_DOMAIN}",
                body=self.sync_service._group_settings(False),
            )

            self.directory_api.members().list.assert_called()
            self.directory_api.groups().aliases().list.assert_called()

        self.settings_api.reset_mock()
        self.directory_api.reset_mock()

        with self.subTest("Failure"):
            self.directory_api.groups().insert().execute.side_effect = HttpError(
                Response({"status": 500}), bytes()
            )

            self.sync_service.create_group(
                GSuiteSyncService.GroupData(
                    "new_group",
                    "some description",
                    False,
                    ["alias2"],
                    [f"test2@{settings.GSUITE_DOMAIN}"],
                )
            )

            self.directory_api.members().list.assert_not_called()
            self.directory_api.groups().aliases().list.assert_not_called()

            logger_mock.error.assert_called_once_with(
                "Could not successfully finish creating the list new_group", bytes()
            )

    @mock.patch("mailinglists.gsuite.logger")
    def test_update_group(self, logger_mock):
        with self.subTest("Successful"):
            self.sync_service.update_group(
                "new_group",
                GSuiteSyncService.GroupData(
                    "new_group",
                    "some description",
                    False,
                    ["alias2"],
                    [f"test2@{settings.GSUITE_DOMAIN}"],
                ),
            )

            self.directory_api.groups().update.assert_called_once_with(
                body={
                    "email": f"new_group@{settings.GSUITE_DOMAIN}",
                    "name": "new_group",
                    "description": "some description",
                },
                groupKey=f"new_group@{settings.GSUITE_DOMAIN}",
            )

            self.settings_api.groups().update.assert_called_once_with(
                groupUniqueId=f"new_group@{settings.GSUITE_DOMAIN}",
                body=self.sync_service._group_settings(False),
            )

            self.directory_api.members().list.assert_called()
            self.directory_api.groups().aliases().list.assert_called()

        self.settings_api.reset_mock()
        self.directory_api.reset_mock()

        with self.subTest("Failure"):
            self.directory_api.groups().update().execute.side_effect = HttpError(
                Response({"status": 500}), bytes()
            )

            self.sync_service.update_group(
                "new_group",
                GSuiteSyncService.GroupData(
                    "new_group",
                    "some description",
                    False,
                    ["alias2"],
                    [f"test2@{settings.GSUITE_DOMAIN}"],
                ),
            )

            self.directory_api.members().list.assert_not_called()
            self.directory_api.groups().aliases().list.assert_not_called()

            logger_mock.error.assert_called_once_with(
                "Could not update list new_group", bytes()
            )

    @mock.patch("mailinglists.gsuite.logger")
    def test_delete_group(self, logger_mock):
        with self.subTest("Successful"):
            self.sync_service.delete_group("new_group")

            self.settings_api.groups().patch.assert_called_once_with(
                body={"archiveOnly": "true", "whoCanPostMessage": "NONE_CAN_POST"},
                groupUniqueId=f"new_group@{settings.GSUITE_DOMAIN}",
            )

            self.directory_api.members().list.assert_called()
            self.directory_api.groups().aliases().list.assert_called()

        self.settings_api.reset_mock()
        self.directory_api.reset_mock()

        with self.subTest("Failure"):
            self.settings_api.groups().patch().execute.side_effect = HttpError(
                Response({"status": 500}), bytes()
            )

            self.sync_service.delete_group("new_group")

            self.directory_api.members().list.assert_not_called()
            self.directory_api.groups().aliases().list.assert_not_called()

            logger_mock.error.assert_called_once_with(
                "Could not delete list new_group", bytes()
            )

    @mock.patch("mailinglists.gsuite.logger")
    def test_update_group_aliases(self, logger_mock):
        with self.subTest("Error getting existing list"):
            self.directory_api.groups().aliases().list().execute.side_effect = HttpError(
                Response({"status": 500}), bytes()
            )
            self.sync_service._update_group_aliases(
                GSuiteSyncService.GroupData(name="update_group")
            )

            logger_mock.error.assert_called_once_with(
                "Could not obtain existing aliases for list update_group", bytes()
            )

        self.directory_api.reset_mock()

        with self.subTest("Successful with some errors"):
            group_data = GSuiteSyncService.GroupData(
                name="update_group",
                aliases=["not_synced", "not_synced_error", "already_synced"],
            )

            existing_aliases = [
                {"alias": f"deleteme@{settings.GSUITE_DOMAIN}"},
                {"alias": f"deleteme_error@{settings.GSUITE_DOMAIN}"},
                {"alias": f"already_synced@{settings.GSUITE_DOMAIN}"},
            ]

            self.directory_api.groups().aliases().list().execute.side_effect = [
                {"aliases": existing_aliases}
            ]

            self.directory_api.groups().aliases().insert().execute.side_effect = [
                "success",
                HttpError(Response({"status": 500}), bytes()),
            ]

            self.directory_api.groups().aliases().delete().execute.side_effect = [
                "success",
                HttpError(Response({"status": 500}), bytes()),
            ]

            self.sync_service._update_group_aliases(group_data)

            self.directory_api.groups().aliases().insert.assert_any_call(
                groupKey=f"update_group@{settings.GSUITE_DOMAIN}",
                body={"alias": f"not_synced@{settings.GSUITE_DOMAIN}"},
            )

            self.directory_api.groups().aliases().delete.assert_any_call(
                groupKey=f"update_group@{settings.GSUITE_DOMAIN}",
                alias=f"deleteme@{settings.GSUITE_DOMAIN}",
            )

            logger_mock.error.assert_any_call(
                "Could not insert alias not_synced_error@"
                f"{settings.GSUITE_DOMAIN} for list update_group",
                bytes(),
            )

            logger_mock.error.assert_any_call(
                "Could not remove alias deleteme_error@"
                f"{settings.GSUITE_DOMAIN} for list update_group",
                bytes(),
            )

    @mock.patch("mailinglists.gsuite.logger")
    def test_update_group_members(self, logger_mock):
        with self.subTest("Error getting existing list"):
            self.directory_api.members().list().execute.side_effect = HttpError(
                Response({"status": 500}), bytes()
            )
            self.sync_service._update_group_members(
                GSuiteSyncService.GroupData(name="update_group")
            )

            logger_mock.error.assert_called_once_with(
                "Could not obtain list member data", bytes()
            )

        self.directory_api.reset_mock()

        with self.subTest("Successful with some errors"):
            group_data = GSuiteSyncService.GroupData(
                name="update_group",
                addresses=[
                    "not_synced@example.com",
                    "not_synced_error@example.com",
                    "already_synced@example.com",
                ],
            )

            existing_aliases = [
                {"email": "deleteme@example.com", "role": "MEMBER"},
                {"email": "deleteme_error@example.com", "role": "MEMBER"},
                {"email": "already_synced@example.com", "role": "MEMBER"},
                {"email": "donotdelete@example.com", "role": "MANAGER"},
            ]

            self.directory_api.members().list().execute.side_effect = [
                {"members": existing_aliases[:1], "nextPageToken": "some_token"},
                {"members": existing_aliases[1:]},
            ]

            self.directory_api.members().insert().execute.side_effect = [
                "success",
                HttpError(Response({"status": 500}), bytes()),
            ]

            self.directory_api.members().delete().execute.side_effect = [
                "success",
                HttpError(Response({"status": 500}), bytes()),
            ]

            self.sync_service._update_group_members(group_data)

            self.directory_api.members().insert.assert_any_call(
                groupKey=f"update_group@{settings.GSUITE_DOMAIN}",
                body={"email": "not_synced@example.com", "role": "MEMBER"},
            )

            self.directory_api.members().delete.assert_any_call(
                groupKey=f"update_group@{settings.GSUITE_DOMAIN}",
                memberKey="deleteme@example.com",
            )

            self.directory_api.members().delete.assert_not_called_with(
                groupKey=f"update_group@{settings.GSUITE_DOMAIN}",
                memberKey="donotdelete@example.com",
            )

            logger_mock.error.assert_any_call(
                "Could not insert list member "
                "not_synced_error@example.com in update_group",
                bytes(),
            )

            logger_mock.error.assert_any_call(
                "Could not remove list member "
                "deleteme_error@example.com from update_group",
                bytes(),
            )

    @mock.patch("mailinglists.gsuite.logger")
    def test_sync_mailinglists(self, logger_mock):
        original_create = self.sync_service.create_group
        original_update = self.sync_service.update_group
        original_delete = self.sync_service.delete_group

        self.sync_service.create_group = MagicMock()
        self.sync_service.update_group = MagicMock()
        self.sync_service.delete_group = MagicMock()

        with self.subTest("Error getting existing list"):
            self.directory_api.groups().list().execute.side_effect = HttpError(
                Response({"status": 500}), bytes()
            )
            self.sync_service.sync_mailinglists()

            logger_mock.error.assert_called_once_with(
                "Could not get the existing groups", bytes()
            )

        self.directory_api.reset_mock()

        with self.subTest("Successful"):
            existing_groups = [
                {"name": "deleteme", "directMembersCount": "3"},
                {"name": "already_synced", "directMembersCount": "2"},
                {"name": "ignore", "directMembersCount": "0"},
            ]

            self.directory_api.groups().list().execute.side_effect = [
                {"groups": existing_groups[:1], "nextPageToken": "some_token"},
                {"groups": existing_groups[1:]},
            ]

            self.sync_service.sync_mailinglists(
                [
                    GSuiteSyncService.GroupData(name="syncme", addresses=["someone"]),
                    GSuiteSyncService.GroupData(
                        name="already_synced", addresses=["someone"]
                    ),
                    GSuiteSyncService.GroupData(name="ignore2", addresses=[]),
                ]
            )

            self.sync_service.create_group.assert_called_with(
                GSuiteSyncService.GroupData(name="syncme", addresses=["someone"])
            )

            self.sync_service.update_group.assert_called_with(
                "already_synced",
                GSuiteSyncService.GroupData(
                    name="already_synced", addresses=["someone"]
                ),
            )

            self.sync_service.delete_group.assert_called_with("deleteme")

            self.sync_service.create_group.assert_not_called_with(
                GSuiteSyncService.GroupData(name="ignore2", addresses=[])
            )
            self.sync_service.update_group.assert_not_called_with(
                "ignore2", GSuiteSyncService.GroupData(name="ignore2", addresses=[])
            )
            self.sync_service.delete_group.assert_not_called_with("ignore2")

        self.sync_service.create_group = original_create
        self.sync_service.update_group = original_update
        self.sync_service.delete_group = original_delete
