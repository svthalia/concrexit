"""GSuite syncing helpers defined by the mailinglists package."""
import logging
from random import random
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
    """Service for syncing groups and settings for Google Groups."""

    class GroupData:
        """Store data for GSuite groups to sync them."""

        def __init__(
            self,
            name,
            description="",
            moderated=False,
            aliases=ImmutableList([]),
            addresses=ImmutableList([]),
            active_name=None,
        ):
            """Create group data to sync with Gsuite.

            :param name: Name of group
            :param description: Description of group
            :param aliases: Aliases of group
            :param addresses: Addresses in group
            """
            super().__init__()
            self.moderated = moderated
            self.name = name
            self.active_name = active_name
            self.description = description
            self.aliases = aliases
            self.addresses = sorted(set(addresses))

        def __eq__(self, other):
            """Compare group data by comparing properties.

            :param other: Group to compare with
            :return: True if groups are equal, otherwise False.
            """
            if isinstance(other, self.__class__):
                return self.__dict__ == other.__dict__
            return False

    def __init__(
        self,
        groups_settings_api=None,
        directory_api=None,
    ):
        """Create GSuite Sync Service.

        :param groups_settings_api: Group settings API object
        :param directory_api: Directory API object
        """
        self._groups_settings_api = groups_settings_api or get_groups_settings_api()
        self._directory_api = directory_api or get_directory_api()

    @staticmethod
    def _group_settings(moderated):
        """Get group settings dictionary.

        :param moderated: Set the group to be moderated or not
        :return: The group settings dictionary
        """
        return {
            "allowExternalMembers": "true",
            "allowWebPosting": "true",
            "archiveOnly": "false",
            "enableCollaborativeInbox": "true",
            "isArchived": "true",
            "membersCanPostAsTheGroup": "true",
            "messageModerationLevel": "MODERATE_ALL_MESSAGES"
            if moderated
            else "MODERATE_NONE",
            "replyTo": "REPLY_TO_SENDER",
            "whoCanAssistContent": "ALL_MEMBERS",
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
        """Create a new group based on the provided data.

        :param group: GroupData to create a group for
        """
        try:
            self._directory_api.groups().insert(
                body={
                    "email": f"{group.name}@{settings.GSUITE_DOMAIN}",
                    "name": group.name,
                    "description": group.description,
                },
            ).execute()
            # Wait for mailing list creation to complete Docs say we need to
            # wait a minute.
            n = 0
            while True:
                sleep(min(2**n + random(), 64))
                try:
                    self._groups_settings_api.groups().update(
                        groupUniqueId=f"{group.name}@{settings.GSUITE_DOMAIN}",
                        body=self._group_settings(group.moderated),
                    ).execute()
                    break
                except HttpError as e:
                    if n > 6:
                        raise e
                    n += 1
        except HttpError:
            logger.exception(
                f"Could not successfully finish creating the list {group.name}:"
            )
            return False

        self._update_group_members(group)
        self._update_group_aliases(group)

        return True

    def update_group(self, active_name, group):
        """Update a group based on the provided name and data.

        :param active_name: old group name
        :param group: new group data
        """
        try:
            self._directory_api.groups().update(
                groupKey=f"{active_name}@{settings.GSUITE_DOMAIN}",
                body={
                    "email": f"{group.name}@{settings.GSUITE_DOMAIN}",
                    "name": group.name,
                    "description": group.description,
                },
            ).execute()
            self._groups_settings_api.groups().update(
                groupUniqueId=f"{group.name}@{settings.GSUITE_DOMAIN}",
                body=self._group_settings(group.moderated),
            ).execute()
            logger.info(f"List {group.name} updated")
        except HttpError:
            logger.exception(f"Could not update list {group.name}")
            return

        self._update_group_members(group)
        self._update_group_aliases(group)

        MailingList.objects.filter(active_gsuite_name=active_name).update(
            active_gsuite_name=group.name
        )

    def _update_group_aliases(self, group):
        """Update the aliases of a group based on existing values.

        :param group: group data
        """
        try:
            aliases_response = (
                self._directory_api.groups()
                .aliases()
                .list(
                    groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}",
                )
                .execute()
            )
        except HttpError:
            logger.exception(
                f"Could not obtain existing aliases for list {group.name}:"
            )
            return

        existing_aliases = [a["alias"] for a in aliases_response.get("aliases", [])]
        new_aliases = [f"{a}@{settings.GSUITE_DOMAIN}" for a in group.aliases]

        remove_list = [x for x in existing_aliases if x not in new_aliases]
        insert_list = [x for x in new_aliases if x not in existing_aliases]

        batch = self._directory_api.new_batch_http_request()
        for remove_alias in remove_list:
            batch.add(
                self._directory_api.groups()
                .aliases()
                .delete(
                    groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}",
                    alias=remove_alias,
                )
            )

        try:
            batch.execute()
        except HttpError:
            logger.exception(f"Could not remove an alias for list {group.name}")

        batch = self._directory_api.new_batch_http_request()
        for insert_alias in insert_list:
            batch.add(
                self._directory_api.groups()
                .aliases()
                .insert(
                    groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}",
                    body={"alias": insert_alias},
                )
            )

        try:
            batch.execute()
        except HttpError:
            logger.exception(f"Could not insert an alias for list {group.name}")

        logger.info(f"List {group.name} aliases updated")

    def archive_group(self, name):
        """Archive the given mailing list.

        :param name: Group name
        :return: True if the operation succeeded, False otherwise.
        """
        try:
            self._groups_settings_api.groups().patch(
                groupUniqueId=f"{name}@{settings.GSUITE_DOMAIN}",
                body={"archiveOnly": "true", "whoCanPostMessage": "NONE_CAN_POST"},
            ).execute()
            self._update_group_members(GSuiteSyncService.GroupData(name, addresses=[]))
            self._update_group_aliases(GSuiteSyncService.GroupData(name, aliases=[]))
            logger.info(f"List {name} archived")
            return True
        except HttpError:
            logger.exception(f"Could not archive list {name}")
            return False

    def delete_group(self, name):
        """Delete the given mailing list.

        :param name: Group name
        :return: True if the operation succeeded, False otherwise.
        """
        try:
            self._directory_api.groups().delete(
                groupKey=f"{name}@{settings.GSUITE_DOMAIN}",
            ).execute()
            logger.info(f"List {name} deleted")
            return True
        except HttpError:
            logger.exception(f"Could not delete list {name}")
            return False

    def _update_group_members(self, group):
        """Update the group members of the specified group based on the existing members.

        :param group: group data
        """
        try:
            members_response = (
                self._directory_api.members()
                .list(
                    groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}",
                )
                .execute()
            )
            members_list = members_response.get("members", [])
            while "nextPageToken" in members_response:
                members_response = (
                    self._directory_api.members()
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
        except HttpError:
            logger.exception(f"Could not obtain list member data for {group.name}")
            return  # the list does not exist or something else is wrong
        new_members = group.addresses

        remove_list = [x for x in existing_members if x not in new_members]
        insert_list = [
            x
            for x in new_members
            if x not in existing_members and x not in existing_managers
        ]

        batch = self._directory_api.new_batch_http_request()
        for remove_member in remove_list:
            batch.add(
                self._directory_api.members().delete(
                    groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}",
                    memberKey=remove_member,
                )
            )

        try:
            batch.execute()
        except HttpError:
            logger.exception(f"Could not remove a list member from {group.name}")

        batch = self._directory_api.new_batch_http_request()
        for insert_member in insert_list:
            batch.add(
                self._directory_api.members().insert(
                    groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}",
                    body={"email": insert_member, "role": "MEMBER"},
                )
            )

        try:
            batch.execute()
        except HttpError:
            logger.exception(f"Could not insert a list member in {group.name}")

        logger.info(f"List {group.name} members updated")

    @staticmethod
    def mailing_list_to_group(mailing_list):
        """Convert a mailing list model to everything we need for GSuite."""
        return GSuiteSyncService.GroupData(
            name=mailing_list.name,
            moderated=mailing_list.moderated,
            description=mailing_list.description,
            aliases=(
                [x.alias for x in mailing_list.aliases.all()]
                if mailing_list.pk is not None
                else []
            ),
            addresses=(
                list(mailing_list.all_addresses())
                if mailing_list.pk is not None
                else []
            ),
            active_name=mailing_list.active_gsuite_name,
        )

    @staticmethod
    def _automatic_to_group(automatic_list):
        """Convert an automatic mailinglist to a GSuite Group data obj."""
        return GSuiteSyncService.GroupData(
            moderated=automatic_list["moderated"],
            name=automatic_list["name"],
            description=automatic_list["description"],
            aliases=automatic_list.get("aliases", []),
            addresses=automatic_list["addresses"],
        )

    def _get_default_lists(self):
        return [self.mailing_list_to_group(ml) for ml in MailingList.objects.all()] + [
            self._automatic_to_group(ml) for ml in get_automatic_lists()
        ]

    def sync_mailing_lists(self, lists: List[GroupData] = None):
        """Sync mailing lists with GSuite. Lists are only deleted if all lists are synced and thus no lists are passed to this function.

        :param lists: optional parameter to determine which lists to sync
        """
        if lists is None:
            lists = self._get_default_lists()

        try:
            groups_response = (
                self._directory_api.groups()
                .list(domain=settings.GSUITE_DOMAIN)
                .execute()
            )
            groups_list = groups_response.get("groups", [])
            while "nextPageToken" in groups_response:
                groups_response = (
                    self._directory_api.groups()
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
        except HttpError:
            logger.exception("Could not get the existing groups")
            return  # there are no groups or something went wrong

        new_groups = [
            g.active_name if g.active_name else g.name
            for g in lists
            if len(g.addresses) > 0
        ]

        archive_list = [x for x in existing_groups if x not in new_groups]
        insert_list = [x for x in new_groups if x not in existing_groups]

        for mailinglist in lists:
            if (
                mailinglist.name in insert_list
                and mailinglist.name not in archived_groups
            ):
                logger.debug(f"Starting create group of {mailinglist.name}")
                if self.create_group(mailinglist):
                    MailingList.objects.filter(name=mailinglist.name).update(
                        active_gsuite_name=mailinglist.name
                    )
            elif len(mailinglist.addresses) > 0:
                logger.debug(f"Starting update group of {mailinglist.name}")
                self.update_group(
                    mailinglist.active_name
                    if mailinglist.active_name
                    else mailinglist.name,
                    mailinglist,
                )

        for list_name in archive_list:
            if list_name in existing_groups:
                logger.debug(f"Starting archive group of {list_name}")
                self.archive_group(list_name)

        logger.info("Synchronisation ended.")
