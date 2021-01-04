import logging
import os
from subprocess import Popen

from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class ThaliaWebsiteConfig(AppConfig):
    name = "thaliawebsite"

    def ready(self):
        if (
            settings.DJANGO_ENV in ["production", "staging"]
            and os.environ.get("MANAGE_PY", "0") == "0"
        ):
            logger.info("Telling systemd we're ready")
            try:
                Popen(
                    [
                        "/run/current-system/sw/bin/systemd-notify",
                        "--ready",
                        "--status=App registry populated",
                    ]
                )
            except Exception as e:  # pylint: disable=broad-except
                logger.exception(e)
