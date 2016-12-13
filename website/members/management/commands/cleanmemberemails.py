from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.core.validators import validate_email


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry-run',
            default=False,
            help='Dry run instead of saving data',
        )

    def handle(self, *args, **options):

        users = User.objects.all()

        for user in users:
            try:
                validate_email(user.email)
            except ValidationError:
                print("Email address for " + user.username +
                      " invalid: " + user.email)
                if not options['dry-run']:
                    user.email = ""
                    user.save()
