import logging
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand

try:
    from faker import Factory as FakerFactory
except ImportError as error:
    raise ValueError(
        f"Have you installed the dev-requirements? Failed importing {error}"
    ) from error

_faker = FakerFactory.create("nl_NL")
logger = logging.getLogger(__name__)

_PASSWORD_CHARS = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class Command(BaseCommand):
    """Command to create a user we can use to review."""

    help = "Creates a user for the a review environment"

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            dest="username",
            default=None,
            help="Specifies the username for the user.",
        )
        parser.add_argument(
            "--password",
            dest="password",
            default=None,
            help="Specifies the password for the user.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            logger.info("Cannot create review user in production mode")
            return

        username = options.get("username")
        password = options.get("password")

        if username is None:
            username = _faker.user_name()
        if password is None:
            password = "".join(secrets.choice(_PASSWORD_CHARS) for _ in range(15))

        get_user_model().objects.create_superuser(
            username=username,
            email=f"{username}@example.com",
            password=password,
            first_name="Riley",
            last_name="Review",
        )

        logger.info("Username: %s", username)
        logger.info("Password: %s", password)
