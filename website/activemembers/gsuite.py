import hashlib
import logging
from base64 import b16encode

from django.utils.translation import (
    ugettext_lazy as _, override as lang_override
)
from googleapiclient.errors import HttpError

from members.models import Member
from utils.google_api import get_directory_api
from django.conf import settings

logger = logging.getLogger(__name__)


class GSuiteUserService:
    def __init__(self, directory_api=get_directory_api()):
        super().__init__()
        self.directory_api = directory_api

    def create_user(self, member: Member):
        """
        Create a new GSuite user based on the provided data
        :param member: The member that gets an account
        :return returns a tuple with the password and id of the created user
        """
        plain_password = Member.objects.make_random_password(15)
        digest_password = hashlib.sha1(plain_password.encode('utf-8')).digest()
        encoded_password = b16encode(digest_password).decode("utf-8")

        try:
            response = self.directory_api.users().insert(
                body={
                    'name': {
                        'familyName': member.last_name,
                        'givenName': member.first_name
                    },
                    'primaryEmail':
                        f'{member.username}@{settings.GSUITE_MEMBERS_DOMAIN}',
                    'password': encoded_password,
                    'hashFunction': 'SHA-1',
                    'changePasswordAtNextLogin': 'true',
                    'externalIds': [{
                        'value': f'{member.pk}',
                        'type': 'login_id'
                    }],
                    'includeInGlobalAddressList': 'false',
                    'orgUnitPath': '/',
                },
            ).execute()
        except HttpError as e:
            if e.resp.status == 409:
                return self.update_user(member, member.username)
            raise e

        return response['primaryEmail'], plain_password

    def update_user(self, member: Member, username: str):
        response = self.directory_api.users().patch(
            body={
                'suspended': 'false',
                'primaryEmail':
                    f'{member.username}@{settings.GSUITE_MEMBERS_DOMAIN}',
            },
            userKey=f'{username}@{settings.GSUITE_MEMBERS_DOMAIN}'
        ).execute()

        if username != member.username:
            self.directory_api.users().aliases().delete(
                userKey=f'{member.username}@{settings.GSUITE_MEMBERS_DOMAIN}',
                alias=f'{username}@{settings.GSUITE_MEMBERS_DOMAIN}',
            ).execute()

        with lang_override(member.profile.language):
            password = _('known by the user')

        return response['primaryEmail'], password

    def suspend_user(self, username):
        """
        Suspends the user in GSuite
        :param username: username of the user
        """
        self.directory_api.users().patch(
            body={
                'suspended': 'true',
            },
            userKey=f'{username}@{settings.GSUITE_MEMBERS_DOMAIN}'
        ).execute()

    def delete_user(self, email):
        """
        Deletes the user from GSuite
        :param email: primary email of the user
        """
        self.directory_api.users().delete(
            userKey=email
        ).execute()

    def get_suspended_users(self):
        """
        Get all the suspended users
        :return:
        """
        response = self.directory_api.users().list(
            domain=settings.GSUITE_MEMBERS_DOMAIN,
            query='isSuspended=true'
        ).execute()
        return response.get('users', [])
