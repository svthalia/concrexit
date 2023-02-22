import logging
import threading
from typing import Generator

from moneybird.administration import (
    Administration,
    get_moneybird_administration,
)
from moneybird.resource_types import (
    MoneybirdResourceId,
    MoneybirdResourceVersion,
    MoneybirdResourceType,
    SynchronizableMoneybirdResourceType,
    get_moneybird_resources,
)

MAX_REQUEST_SIZE = 100

sync_lock = threading.Lock()


class MoneybirdSync:
    @staticmethod
    def __chunks(lst: list, chunk_size: int) -> Generator[list, None, None]:
        """Split a list into chunks of size chunk_size."""
        for idx in range(0, len(lst), chunk_size):
            yield lst[idx : idx + chunk_size]

    def __init__(self, administration: Administration):
        self.administration = administration

    def get_resource_versions(
        self, resource_type: SynchronizableMoneybirdResourceType
    ) -> dict[MoneybirdResourceId, MoneybirdResourceVersion]:
        objects = self.administration.get(
            resource_type.get_synchronization_api_endpoint()
        )
        return {instance["id"]: instance["version"] for instance in objects}

    def _get_resources_by_id_paginated(
        self,
        resource_type: SynchronizableMoneybirdResourceType,
        ids: list[MoneybirdResourceId],
    ):
        assert len(ids) <= MAX_REQUEST_SIZE
        response = self.administration.post(
            resource_type.get_synchronization_api_endpoint(), data={"ids": ids}
        )
        return response

    def get_resources_by_id(
        self,
        resource_type: SynchronizableMoneybirdResourceType,
        ids: list[MoneybirdResourceId],
    ):
        """Get an iterator over all resources of a given type."""
        if len(ids) == 0:
            return []
        for id_chunk in self.__chunks(ids, MAX_REQUEST_SIZE):
            try:
                response = self._get_resources_by_id_paginated(resource_type, id_chunk)
                yield from response
            except Administration.Throttled:
                logging.warning("Throttled, stopping sync")
                break

    def get_all_resources_paginated(self, resource_type: MoneybirdResourceType):
        params = resource_type.get_all_resources_api_endpoint_params()
        if params is None:
            params = {}
        params["page"] = 1

        resources = []

        while True:
            response = self.administration.get(
                resource_type.get_all_resources_api_endpoint(),
                params=params,
            )
            resources.extend(response)

            if len(response) < resource_type.pagination_size:
                return resources

            params["page"] += 1

    def get_all_resources(self, resource_type: MoneybirdResourceType):
        if resource_type.paginated:
            return self.get_all_resources_paginated(resource_type)
        return self.administration.get(
            resource_type.get_all_resources_api_endpoint(),
            params=resource_type.get_all_resources_api_endpoint_params(),
        )

    def sync_using_synchronization_endpoint_efficient(
        self, resource_type: SynchronizableMoneybirdResourceType
    ):
        local_versions = resource_type.get_local_versions()
        remote_versions = self.get_resource_versions(resource_type)
        resources_to_sync = SynchronizableMoneybirdResourceType.diff_resource_versions(
            local_versions, remote_versions
        )

        resource_type.queryset_delete_from_moneybird(resources_to_sync.removed)

        new_resources = self.get_resources_by_id(resource_type, resources_to_sync.added)
        for resource in new_resources:
            resource_type.create_from_moneybird(resource)

        updated_resources = self.get_resources_by_id(
            resource_type, resources_to_sync.changed
        )
        for resource in updated_resources:
            resource_type.update_from_moneybird(resource)

    def sync_naive(self, resource_type: MoneybirdResourceType):
        local_versions = resource_type.get_local_versions()
        resources = self.get_all_resources(resource_type)
        changes = MoneybirdResourceType.diff_resources(local_versions, resources)
        logging.info(f"Updating {resource_type.__name__} resources with changes")
        resource_type.update_resources(changes)

    def sync_resource_type(self, resource_type: MoneybirdResourceType):
        """Perform a full sync of a resource type."""
        if not resource_type.can_do_full_sync:
            logging.info(f"{resource_type.__name__} cannot be fully synchronized")
            return None

        resource_type.get_queryset().filter(moneybird_id__isnull=True).delete()

        logging.info(f"Start fetching {resource_type.__name__} from Moneybird")

        if issubclass(resource_type, SynchronizableMoneybirdResourceType):
            self.sync_using_synchronization_endpoint_efficient(resource_type)
        else:
            self.sync_naive(resource_type)

        logging.info(f"Finished synchronizing {resource_type.__name__}")

    def push_unsynced(self, resource_type: MoneybirdResourceType):
        """Push all unsynced moneybird resources."""
        for resource in resource_type.get_queryset().filter(
            _synced_with_moneybird=False
        ):
            try:
                resource.push_to_moneybird()
            except Exception as e:
                logging.error(f"Failed to push {resource_type.__name__} {resource.id}")
                logging.error(e)
                try:
                    resource.refresh_from_moneybird()
                except Exception as e:
                    logging.error(
                        f"Failed to refresh {resource_type.__name__} {resource.id}"
                    )
                    logging.error(e)
                    resource.delete(received_from_moneybird=True)
                    continue

    def perform_sync(self, resource_types: list[MoneybirdResourceType]):
        """Perform a full sync of a list of resources."""
        for resource_type in resource_types:
            self.push_unsynced(resource_type)
            self.sync_resource_type(resource_type)


def synchronize(full_sync=False) -> None:
    locked = sync_lock.acquire(blocking=False)
    if locked:
        try:
            resource_types = get_moneybird_resources()
            administration = get_moneybird_administration()
            if full_sync:
                for resource_type in resource_types:
                    if issubclass(resource_type, SynchronizableMoneybirdResourceType):
                        resource_type.get_queryset().update(moneybird_version=None)

            MoneybirdSync(administration).perform_sync(resource_types)
        finally:
            sync_lock.release()
