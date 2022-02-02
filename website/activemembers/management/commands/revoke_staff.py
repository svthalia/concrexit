from django.core.management.base import BaseCommand

from activemembers.services import revoke_staff_permission_for_users_in_no_commitee


class Command(BaseCommand):
    """This command can be executed daily to check group membership and revoke staff permissions when needed"""

    def handle(self, *args, **options):
        revoked = revoke_staff_permission_for_users_in_no_commitee()
        for member in revoked:
            self.stdout.write("Revoked staff permissions for {}".format(member))
