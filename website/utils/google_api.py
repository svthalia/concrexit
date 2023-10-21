from django.conf import settings

from googleapiclient.discovery import build
from googleapiclient.discovery_cache.base import Cache


class MemoryCache(Cache):
    _CACHE = {}

    def get(self, url):
        return MemoryCache._CACHE.get(url)

    def set(self, url, content):
        MemoryCache._CACHE[url] = content


memory_cache = MemoryCache()


def get_directory_api():
    return build(
        "admin",
        "directory_v1",
        credentials=settings.GSUITE_ADMIN_CREDENTIALS,
        cache=memory_cache,
    )


def get_groups_settings_api():
    return build(
        "groupssettings",
        "v1",
        credentials=settings.GSUITE_ADMIN_CREDENTIALS,
        cache=memory_cache,
    )
