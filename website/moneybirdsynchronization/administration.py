"""The MoneyBird API.

This code is largely based on moneybird-python by Jan-Jelle Kester,
licensed under the MIT license. The source code of moneybird-python
can be found on GitHub: https://github.com/jjkester/moneybird-python.
"""
import functools
import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from functools import reduce
from urllib.parse import urljoin

from django.conf import settings

import requests

logger = logging.getLogger(__name__)


class Administration(ABC):
    """A MoneyBird administration."""

    administration_id = None

    def __init__(self, administration_id: int):
        self.administration_id = administration_id

    @abstractmethod
    def get(self, resource_path: str, params: dict | None = None):
        """Do a GET on the Moneybird administration."""

    @abstractmethod
    def post(self, resource_path: str, data: dict):
        """Do a POST request on the Moneybird administration."""

    @abstractmethod
    def patch(self, resource_path: str, data: dict):
        """Do a PATCH request on the Moneybird administration."""

    @abstractmethod
    def delete(self, resource_path: str):
        """Do a DELETE request on the Moneybird administration."""

    class InvalidResourcePath(Exception):
        """The given resource path is invalid."""

    class Error(Exception):
        """An exception that can be thrown while using the administration."""

        def __init__(self, status_code: int, description: str | None = None):
            """Create a new administration error."""
            msg = f"API error {status_code}"
            if description:
                msg += f": {description}"

            self.status_code = status_code
            self.description = description

            super().__init__(msg)

    class Unauthorized(Error):
        """The client has insufficient authorization."""

    class NotFound(Error):
        """The client requested a resource that could not be found."""

    class InvalidData(Error):
        """The client sent invalid data."""

    class Throttled(Error):
        """The client sent too many requests."""

        retry_after: int

    class ServerError(Error):
        """An error happened on the server."""

    @abstractmethod
    def _create_session(self) -> requests.Session:
        """Create a new session."""

    def _build_url(self, resource_path: str) -> str:
        if resource_path.startswith("/"):
            raise Administration.InvalidResourcePath(
                "The resource path must not start with a slash."
            )

        api_base_url = "https://moneybird.com/api/v2/"
        url_parts = [
            api_base_url,
            f"{self.administration_id}/",
            f"{resource_path}.json",
        ]
        return reduce(urljoin, url_parts)

    def _process_response(self, response: requests.Response) -> dict | None:
        logger.debug(f"Response {response.status_code}: {response.text}")

        if response.next:
            logger.debug(f"Received paginated response: {response.next}")

        good_codes = {200, 201, 204}
        bad_codes = {
            400: Administration.InvalidData,
            401: Administration.Unauthorized,
            403: Administration.Unauthorized,
            404: Administration.NotFound,
            406: Administration.InvalidData,
            422: Administration.InvalidData,
            429: Administration.Throttled,
            500: Administration.ServerError,
        }

        code = response.status_code

        code_is_known: bool = code in good_codes | bad_codes.keys()

        if not code_is_known:
            logger.warning(f"Unknown response code {code}")
            raise Administration.Error(
                code, "API response contained unknown status code"
            )

        if code in bad_codes:
            error = bad_codes[code]
            if error == Administration.Throttled:
                e = Administration.Throttled(code, "Throttled")
                e.retry_after = response.headers.get("Retry-After")
                e.rate_limit_remaining = response.headers.get("RateLimit-Remaining")
                e.rate_limit_limit = response.headers.get("RateLimit-Limit")
                e.rate_limit_reset = response.headers.get("RateLimit-Reset")
                error_description = f"retry after {e.retry_after}"
            else:
                try:
                    error_description = response.json()["error"]
                except (AttributeError, TypeError, KeyError, ValueError):
                    error_description = None

                e = error(code, error_description)

            logger.warning(f"API error {code}: {e}")

            raise e

        if code == 204:
            return {}

        if response.text == "200":
            return {}

        return response.json()


def _retry_if_throttled():
    max_retries = 3

    def decorator_retry(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except HttpsAdministration.Throttled as e:
                    retries += 1
                    retry_after = datetime.fromtimestamp(float(e.retry_after))
                    now = datetime.now()
                    sleep_seconds = int(retry_after.timestamp() - now.timestamp()) + 1
                    if retries < max_retries:
                        logger.info(f"Retrying in {sleep_seconds} seconds...")
                        time.sleep(sleep_seconds)
                    else:
                        logger.warning("Max retries reached. Giving up.")
            return None

        return wrapper

    return decorator_retry


class HttpsAdministration(Administration):
    """The HTTPS implementation of the MoneyBird Administration interface."""

    def __init__(self, key: str, administration_id: int):
        """Create a new MoneyBird administration connection."""
        super().__init__(administration_id)
        self.key = key
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({"Authorization": f"Bearer {self.key}"})
        return session

    @_retry_if_throttled()
    def get(self, resource_path: str, params: dict | None = None):
        """Do a GET on the Moneybird administration."""
        url = self._build_url(resource_path)
        logger.debug(f"GET {url} {params}")
        response = self.session.get(url, params=params)
        return self._process_response(response)

    @_retry_if_throttled()
    def post(self, resource_path: str, data: dict):
        """Do a POST request on the Moneybird administration."""
        url = self._build_url(resource_path)
        data = json.dumps(data)
        logger.debug(f"POST {url} with {data}")
        response = self.session.post(url, data=data)
        return self._process_response(response)

    @_retry_if_throttled()
    def patch(self, resource_path: str, data: dict):
        """Do a PATCH request on the Moneybird administration."""
        url = self._build_url(resource_path)
        data = json.dumps(data)
        logger.debug(f"PATCH {url} with {data}")
        response = self.session.patch(url, data=data)
        return self._process_response(response)

    @_retry_if_throttled()
    def delete(self, resource_path: str, data: dict | None = None):
        """Do a DELETE on the Moneybird administration."""
        url = self._build_url(resource_path)
        logger.debug(f"DELETE {url}")
        response = self.session.delete(url, data=data)
        return self._process_response(response)


class MoneybirdNotConfiguredError(RuntimeError):
    pass


def get_moneybird_administration():
    if settings.MONEYBIRD_ADMINISTRATION_ID and settings.MONEYBIRD_API_KEY:
        return HttpsAdministration(
            settings.MONEYBIRD_API_KEY, settings.MONEYBIRD_ADMINISTRATION_ID
        )
    raise MoneybirdNotConfiguredError()
