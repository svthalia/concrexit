import hashlib
import logging
from django.conf import settings
from django.utils.translation import gettext_lazy as _, override as lang_override

from googleapiclient.errors import HttpError

from members.models import Member
from utils.google_api import get_directory_api

logger = logging.getLogger(__name__)


class GSuiteUserService:
    def __init__(self, directory_api=None):
        self._directory_api = directory_api

    @property
    def directory_api(self):
        if self._directory_api is not None:
            return self._directory_api
        return get_directory_api()

    def create_user(self, member: Member):
        """Create a new GSuite user based on the provided data.

        :param member: The member that gets an account
        :return returns a tuple with the password and id of the created user
        """
        plain_password = Member.objects.make_random_password(length=15)

        # Google only supports sha-1, md5 or crypt as hash functions[0] for the initial password.
        # Because this password should be changed on first login and is safely sent to Google over
        # https, we just use sha-1 for simplicity. GitHub code scanning gave a warning about this
        # but we have set it to ignore the 'problem'.
        # [0]: https://developers.google.com/admin-sdk/directory/reference/rest/v1/users#User.FIELDS.hash_function
        digest_password = hashlib.sha1(plain_password.encode("utf-8")).hexdigest()

        try:
            response = (
                self.directory_api.users()
                .insert(
                    body={
                        "name": {
                            "familyName": member.last_name,
                            "givenName": member.first_name,
                        },
                        "primaryEmail": f"{member.username}@{settings.GSUITE_MEMBERS_DOMAIN}",
                        "password": digest_password,
                        "hashFunction": "SHA-1",
                        "changePasswordAtNextLogin": "true",
                        "externalIds": [{"value": f"{member.pk}", "type": "login_id"}],
                        "includeInGlobalAddressList": "false",
                        "orgUnitPath": "/",
                    },
                )
                .execute()
            )
        except HttpError as e:
            if e.resp.status == 409:
                return self.update_user(member, member.username)
            raise e

        return response["primaryEmail"], plain_password

    def update_user(self, member: Member, username: str):
        response = (
            self.directory_api.users()
            .patch(
                body={
                    "suspended": "false",
                    "primaryEmail": f"{member.username}@{settings.GSUITE_MEMBERS_DOMAIN}",
                },
                userKey=f"{username}@{settings.GSUITE_MEMBERS_DOMAIN}",
            )
            .execute()
        )

        if username != member.username:
            self.directory_api.users().aliases().delete(
                userKey=f"{member.username}@{settings.GSUITE_MEMBERS_DOMAIN}",
                alias=f"{username}@{settings.GSUITE_MEMBERS_DOMAIN}",
            ).execute()

        return response["primaryEmail"], _("known by the user")

    def suspend_user(self, username):
        """Suspend the user in GSuite.

        :param username: username of the user
        """
        self.directory_api.users().patch(
            body={"suspended": "true",},
            userKey=f"{username}@{settings.GSUITE_MEMBERS_DOMAIN}",
        ).execute()

    def delete_user(self, email):
        """Delete the user from GSuite.

        :param email: primary email of the user
        """
        self.directory_api.users().delete(userKey=email).execute()

    def get_suspended_users(self):
        """Get all the suspended users."""
        response = (
            self.directory_api.users()
            .list(domain=settings.GSUITE_MEMBERS_DOMAIN, query="isSuspended=true")
            .execute()
        )
        return response.get("users", [])
