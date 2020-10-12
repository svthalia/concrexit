"""GSuite syncing helpers defined by the mailinglists package"""
import logging
from time import sleep
from typing import List

from django.conf import settings
from django.utils.datastructures import ImmutableList
from googleapiclient.errors import HttpError

from mailinglists.models import MailingList
from mailinglists.services import get_automatic_lists
from utils.google_api import get_directory_api, get_groups_settings_api

logger = logging.getLogger(__name__)


class GSuiteSyncService:
    class GroupData:
        def __init__(
            self,
            name,
            description="",
            moderated=False,
            aliases=ImmutableList([]),
            addresses=ImmutableList([]),
        ):
            super().__init__()
            self.moderated = moderated
            self.name = name
            self.description = description
            self.aliases = aliases
            self.addresses = sorted(set(addresses))

        def __eq__(self, other: object) -> bool:
            if isinstance(other, self.__class__):
                return self.__dict__ == other.__dict__
            return False

    def __init__(
        self,
        groups_settings_api=get_groups_settings_api(),
        directory_api=get_directory_api(),
    ):
        super().__init__()
        self.groups_settings_api = groups_settings_api
        self.directory_api = directory_api

    @staticmethod
    def _group_settings(moderated):
        return {
            "allowExternalMembers": "true",
            "allowWebPosting": "false",
            "archiveOnly": "false",
            "isArchived": "true",
            "membersCanPostAsTheGroup": "false",
            "messageModerationLevel": "MODERATE_ALL_MESSAGES"
            if moderated
            else "MODERATE_NONE",
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
        }

    def create_group(self, group):
        """
        Create a new group based on the provided data
        :param group: group data
        """
        try:
            self.directory_api.groups().insert(
                body={
                    "email": f"{group.name}@{settings.GSUITE_DOMAIN}",
                    "name": group.name,
                    "description": group.description,
                },
            ).execute()
            # Wait for mailinglist creation to complete Docs say we need to
            # wait a minute, but since we always update lists
            # an error in the list members update is not a problem
            sleep(0.5)
            self.groups_settings_api.groups().update(
                groupUniqueId=f"{group.name}@{settings.GSUITE_DOMAIN}",
                body=self._group_settings(group.moderated),
            ).execute()
            logger.info("List %s created", group.name)
        except HttpError as e:
            logger.error(
                "Could not successfully finish creating the list %s: %s",
                group.name,
                e.content,
            )
            return

        self._update_group_members(group)
        self._update_group_aliases(group)

    def update_group(self, old_name, group):
        """
        Update a group based on the provided name and data
        :param old_name: old group name
        :param group: new group data
        """
        try:
            self.directory_api.groups().update(
                groupKey=f"{old_name}@{settings.GSUITE_DOMAIN}",
                body={
                    "email": f"{group.name}@{settings.GSUITE_DOMAIN}",
                    "name": group.name,
                    "description": group.description,
                },
            ).execute()
            self.groups_settings_api.groups().update(
                groupUniqueId=f"{group.name}@{settings.GSUITE_DOMAIN}",
                body=self._group_settings(group.moderated),
            ).execute()
            logger.info("List %s updated", group.name)
        except HttpError as e:
            logger.error("Could not update list %s: %s", group.name, e.content)
            return

        self._update_group_members(group)
        self._update_group_aliases(group)

    def _update_group_aliases(self, group: GroupData):
        """
        Update the aliases of a group based on existing values
        :param group: group data
        """
        try:
            aliases_response = (
                self.directory_api.groups()
                .aliases()
                .list(groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}",)
                .execute()
            )
        except HttpError as e:
            logger.error(
                "Could not obtain existing aliases for list %s: %s",
                group.name,
                e.content,
            )
            return

        existing_aliases = [a["alias"] for a in aliases_response.get("aliases", [])]
        new_aliases = [f"{a}@{settings.GSUITE_DOMAIN}" for a in group.aliases]

        remove_list = [x for x in existing_aliases if x not in new_aliases]
        insert_list = [x for x in new_aliases if x not in existing_aliases]

        for remove_alias in remove_list:
            try:
                self.directory_api.groups().aliases().delete(
                    groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}",
                    alias=remove_alias,
                ).execute()
            except HttpError as e:
                logger.error(
                    "Could not remove alias %s for list %s: %s",
                    remove_alias,
                    group.name,
                    e.content,
                )

        for insert_alias in insert_list:
            try:
                self.directory_api.groups().aliases().insert(
                    groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}",
                    body={"alias": insert_alias},
                ).execute()
            except HttpError as e:
                logger.error(
                    "Could not insert alias %s for list %s: %s",
                    insert_alias,
                    group.name,
                    e.content,
                )

        logger.info("List %s aliases updated", group.name)

    def delete_group(self, name: str):
        """
        Set the specified list to unused, this is not a real delete
        :param name: Group name
        """
        try:
            self.groups_settings_api.groups().patch(
                groupUniqueId=f"{name}@{settings.GSUITE_DOMAIN}",
                body={"archiveOnly": "true", "whoCanPostMessage": "NONE_CAN_POST"},
            ).execute()
            self._update_group_members(GSuiteSyncService.GroupData(name, addresses=[]))
            self._update_group_aliases(GSuiteSyncService.GroupData(name, aliases=[]))
            logger.info("List %s deleted", name)
        except HttpError as e:
            logger.error("Could not delete list %s: %s", name, e.content)

    def _update_group_members(self, group: GroupData):
        """
        Update the group members of the specified group based
        on the existing members
        :param group: group data
        """
        try:
            members_response = (
                self.directory_api.members()
                .list(groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}",)
                .execute()
            )
            members_list = members_response.get("members", [])
            while "nextPageToken" in members_response:
                members_response = (
                    self.directory_api.members()
                    .list(
                        groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}",
                        pageToken=members_response["nextPageToken"],
                    )
                    .execute()
                )
                members_list += members_response.get("members", [])

            existing_members = [
                m["email"] for m in members_list if m["role"] == "MEMBER"
            ]
            existing_managers = [
                m["email"] for m in members_list if m["role"] == "MANAGER"
            ]
        except HttpError as e:
            logger.error("Could not obtain list member data: %s", e.content)
            return  # the list does not exist or something else is wrong
        new_members = group.addresses

        remove_list = [x for x in existing_members if x not in new_members]
        insert_list = [
            x
            for x in new_members
            if x not in existing_members and x not in existing_managers
        ]

        for remove_member in remove_list:
            try:
                self.directory_api.members().delete(
                    groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}",
                    memberKey=remove_member,
                ).execute()
            except HttpError as e:
                logger.error(
                    "Could not remove list member %s from %s: %s",
                    remove_member,
                    group.name,
                    e.content,
                )

        for insert_member in insert_list:
            try:
                self.directory_api.members().insert(
                    groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}",
                    body={"email": insert_member, "role": "MEMBER"},
                ).execute()
            except HttpError as e:
                logger.error(
                    "Could not insert list member %s in %s: %s",
                    insert_member,
                    group.name,
                    e.content,
                )

        logger.info("List %s members updated", group.name)

    @staticmethod
    def mailinglist_to_group(mailinglist: MailingList):
        """Convert a mailinglist model to everything we need for GSuite"""
        return GSuiteSyncService.GroupData(
            moderated=mailinglist.moderated,
            name=mailinglist.name,
            description=mailinglist.description,
            aliases=(
                [x.alias for x in mailinglist.aliases.all()]
                if mailinglist.pk is not None
                else []
            ),
            addresses=(
                list(mailinglist.all_addresses()) if mailinglist.pk is not None else []
            ),
        )

    @staticmethod
    def _automatic_to_group(automatic_list):
        """Convert an automatic mailinglist to a GSuite Group data obj"""
        return GSuiteSyncService.GroupData(
            moderated=automatic_list["moderated"],
            name=automatic_list["name"],
            description=automatic_list["description"],
            aliases=automatic_list.get("aliases", []),
            addresses=automatic_list["addresses"],
        )

    def _get_default_lists(self):
        return [self.mailinglist_to_group(ml) for ml in MailingList.objects.all()] + [
            self._automatic_to_group(ml) for ml in get_automatic_lists()
        ]

    def sync_mailinglists(self, lists: List[GroupData] = None):
        """
        Sync mailing lists with GSuite
        :param lists: optional parameter to determine which lists to sync
        """
        if lists is None:
            lists = self._get_default_lists()

        try:
            groups_response = (
                self.directory_api.groups()
                .list(domain=settings.GSUITE_DOMAIN)
                .execute()
            )
            groups_list = groups_response.get("groups", [])
            while "nextPageToken" in groups_response:
                groups_response = (
                    self.directory_api.groups()
                    .list(
                        domain=settings.GSUITE_DOMAIN,
                        pageToken=groups_response["nextPageToken"],
                    )
                    .execute()
                )
                groups_list += groups_response.get("groups", [])
            existing_groups = [
                g["name"] for g in groups_list if int(g["directMembersCount"]) > 0
            ]
            archived_groups = [
                g["name"] for g in groups_list if g["directMembersCount"] == "0"
            ]
        except HttpError as e:
            logger.error("Could not get the existing groups: %s", e.content)
            return  # there are no groups or something went wrong

        new_groups = [g.name for g in lists if len(g.addresses) > 0]

        remove_list = [x for x in existing_groups if x not in new_groups]
        insert_list = [x for x in new_groups if x not in existing_groups]

        for ml in lists:
            if ml.name in insert_list and ml.name not in archived_groups:
                self.create_group(ml)
            elif len(ml.addresses) > 0:
                self.update_group(ml.name, ml)

        for ml in remove_list:
            self.delete_group(ml)
