import logging

from celery import shared_task

from activemembers.gsuite import GSuiteUserService
from activemembers.services import revoke_staff_permission_for_users_in_no_commitee

logger = logging.getLogger(__name__)
sync_service = GSuiteUserService()


@shared_task
def revoke_staff():
    revoked = revoke_staff_permission_for_users_in_no_commitee()
    for member in revoked:
        logger.info(f"Revoked staff permissions for {member}")


@shared_task
def delete_gsuite_users():
    suspended_users = sync_service.get_suspended_users()
    for user in suspended_users:
        sync_service.delete_user(user["primaryEmail"])
