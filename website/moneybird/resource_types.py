import logging
from dataclasses import dataclass, field

from django.db import IntegrityError
from django.utils.module_loading import import_string

from moneybird.administration import get_moneybird_administration, Administration
from moneybird.settings import settings
from moneybird.webhooks.events import WebhookEvent

MoneybirdResourceId = str
MoneybirdResourceVersion = int
MoneybirdResource = dict


@dataclass
class ResourceDiff:
    added: list[MoneybirdResource] = field(default_factory=list)
    changed: list[MoneybirdResource] = field(default_factory=list)
    removed: list[MoneybirdResourceId] = field(default_factory=list)


@dataclass
class ResourceVersionDiff:
    added: list[MoneybirdResourceId] = field(default_factory=list)
    changed: list[MoneybirdResourceId] = field(default_factory=list)
    removed: list[MoneybirdResourceId] = field(default_factory=list)


class MoneybirdResourceType:
    entity_type = None
    entity_type_name = None
    api_path = None
    public_path = None
    model = None
    can_write = True
    can_delete = True
    can_do_full_sync = True
    paginated = False
    pagination_size = None

    @staticmethod
    def diff_resources(
        old: list[MoneybirdResourceId], new: list[MoneybirdResource]
    ) -> ResourceDiff:
        resources_diff = ResourceDiff()
        resources_diff.added = list(
            filter(lambda resource: resource["id"] not in old, new)
        )
        resources_diff.changed = list(
            filter(lambda resource: resource["id"] in old, new)
        )  # We can only consider every resource has changed if it is in the new list
        resources_diff.removed = list(
            filter(
                lambda resource: resource not in list(r["id"] for r in new),
                old,
            )
        )
        return resources_diff

    @staticmethod
    def calc_data_diff(remote_data, local_data):
        diff = {}
        for key, value in local_data.items():
            if key not in remote_data or value != remote_data[key]:
                diff[key] = value
        return diff

    @staticmethod
    def calc_moneybird_data_diff(new_instance, old_instance):
        new_data = new_instance.serialize_for_moneybird()
        old_data = old_instance.serialize_for_moneybird()

        return MoneybirdResourceType.calc_data_diff(new_data, old_data)

    @classmethod
    def get_all_resources_api_endpoint(cls):
        return cls.api_path

    @classmethod
    def get_all_resources_api_endpoint_params(cls):
        return None

    @classmethod
    def get_queryset(cls):
        return cls.model.objects.all()

    @classmethod
    def get_moneybird_ids(cls) -> list[MoneybirdResourceId]:
        return list(
            map(
                MoneybirdResourceId,
                cls.get_queryset().values_list("moneybird_id", flat=True),
            )
        )

    @classmethod
    def get_local_versions(cls) -> list[MoneybirdResourceId]:
        return cls.get_moneybird_ids()

    @classmethod
    def get_model_kwargs(cls, data):
        return {"moneybird_id": MoneybirdResourceId(data["id"])}

    @classmethod
    def perform_save(cls, obj):
        try:
            obj.save(received_from_moneybird=True)
        except IntegrityError as e:
            try:
                existing_obj = obj.__class_.objects.get(moneybird_id=obj.moneybird_id)
                existing_obj.delete(received_from_moneybird=True)
                obj.save(received_from_moneybird=True)
            except cls.model.DoesNotExist:
                # Apparently, the object exists with the wrong subtype
                existing_obj = obj.__class_.__base__.objects.get(
                    moneybird_id=obj.moneybird_id
                )
                existing_obj.delete(received_from_moneybird=True)
                obj.save(received_from_moneybird=True)

    @classmethod
    def update_resources(cls, diff: ResourceDiff):
        for resource in diff.added:
            cls.create_from_moneybird(resource)
        for resource in diff.changed:
            cls.update_from_moneybird(resource)
        cls.queryset_delete_from_moneybird(diff.removed)

    @classmethod
    def serialize_for_moneybird(cls, instance):
        return {
            "id": MoneybirdResourceId(instance.moneybird_id),
        }

    @classmethod
    def get_or_create_from_moneybird_data(cls, resource_id, data=None):
        if not resource_id:
            return None

        try:
            obj = cls.get_queryset().get(moneybird_id=MoneybirdResourceId(resource_id))
        except cls.model.DoesNotExist:
            logging.info(f"Discovered a new {cls.entity_type_name}, creating it")
            obj = cls.model(moneybird_id=resource_id)
            if data is not None:
                obj.update_fields_from_moneybird(data)
            else:
                try:
                    obj.refresh_from_moneybird()
                except Administration.NotFound:
                    return None
                except Administration.InvalidData:
                    return None
        cls.perform_save(obj)

        return obj

    @classmethod
    def create_instance_from_moneybird(cls, resource_data: MoneybirdResource):
        return cls.model(**cls.get_model_kwargs(resource_data))

    @classmethod
    def create_from_moneybird(cls, resource_data: MoneybirdResource):
        logging.info(f"Adding {cls.entity_type_name} {resource_data['id']}")
        try:
            obj = cls.model.objects.get(
                moneybird_id=MoneybirdResourceId(resource_data["id"])
            )
        except cls.model.DoesNotExist:
            obj = cls.create_instance_from_moneybird(resource_data)
            cls.perform_save(obj)
        return obj

    @classmethod
    def update_from_moneybird(cls, resource_data: MoneybirdResource, obj=None):
        logging.info(f"Updating {cls.entity_type_name} {resource_data['id']}")
        if obj is None:
            try:
                obj = cls.get_queryset().get(
                    moneybird_id=MoneybirdResourceId(resource_data["id"])
                )
            except cls.model.DoesNotExist:
                logging.info(
                    f"{cls.entity_type_name} {resource_data['id']} does not exist, creating it"
                )
                return cls.create_from_moneybird(resource_data), True

        if len(resource_data) > 1:
            # If we get more data than just the id, we need to update the object with the new data
            obj.update_fields_from_moneybird(resource_data)
        cls.perform_save(obj)

        return obj, False

    @classmethod
    def delete_from_moneybird(cls, resource_id: MoneybirdResourceId):
        logging.info(f"Deleting {cls.entity_type_name} {resource_id}")
        try:
            cls.get_queryset().get(
                moneybird_id=MoneybirdResourceId(resource_id)
            ).delete(delete_on_moneybird=False, received_from_moneybird=True)
        except cls.model.DoesNotExist:
            logging.info(
                f"{cls.entity_type_name} {resource_id} does not exist, probably already deleted"
            )

    @classmethod
    def queryset_delete_from_moneybird(cls, ids: list[MoneybirdResourceId]):
        return cls.get_queryset().filter(moneybird_id__in=ids).delete()

    @classmethod
    def queryset_delete(cls, queryset):
        return queryset.update({"_delete_from_moneybird": True})

    @classmethod
    def process_webhook_event(
        cls,
        resource_id: MoneybirdResourceId,
        data: MoneybirdResource,
        event: WebhookEvent,
    ):
        logging.info(f"Processing {event} for {cls.entity_type_name} {resource_id}")
        if not data:
            return cls.delete_from_moneybird(resource_id)
        return cls.update_from_moneybird(data)

    @classmethod
    def get_remote_data_diff(cls, remote_data, local_data):
        return cls.calc_data_diff(remote_data, local_data)

    @classmethod
    def reserialize_without_saving(cls, data):
        obj = cls.create_instance_from_moneybird(data)
        return obj.serialize_for_moneybird()

    @classmethod
    def push_to_moneybird(cls, instance, data=None):
        if not cls.can_write:
            return None

        if data is None:
            if instance.is_synced_with_moneybird:
                return None

            data = cls.serialize_for_moneybird(instance)

        if data == {} or data is None:
            return None

        content = {cls.entity_type_name: data}
        administration = get_moneybird_administration()

        if instance.moneybird_id is None:
            logging.info(f"Creating new {cls.entity_type_name} on Moneybird")
            returned_data = administration.post(cls.api_path, content)
        else:
            if settings.MONEYBIRD_FETCH_BEFORE_PUSH:
                remote_data = administration.get(
                    f"{cls.api_path}/{instance.moneybird_id}"
                )
                remote_data = cls.reserialize_without_saving(remote_data)
                diff = cls.get_remote_data_diff(remote_data, data)
                content = {cls.entity_type_name: diff}

            logging.info(
                f"Updating {cls.entity_type_name} {instance.moneybird_id} on Moneybird"
            )
            returned_data = administration.patch(
                f"{cls.api_path}/{instance.moneybird_id}", content
            )

        if not returned_data or returned_data == {}:
            returned_data = cls.get_from_moneybird(instance)
        else:
            instance.update_fields_from_moneybird(returned_data)

        cls.perform_save(instance)

        return returned_data

    @classmethod
    def push_diff_to_moneybird(cls, instance):
        old_instance = instance.get_from_db()
        if not old_instance:
            return cls.push_to_moneybird(instance)

        diff = cls.calc_moneybird_data_diff(instance, old_instance)
        if diff == {}:
            return

        return cls.push_to_moneybird(instance, diff)

    @classmethod
    def delete_on_moneybird(cls, instance):
        if not cls.can_delete:
            return None
        if not instance.moneybird_id:
            return None

        administration = get_moneybird_administration()

        logging.info(
            f"Deleting {cls.entity_type_name} {instance.moneybird_id} on Moneybird"
        )

        try:
            administration.delete(f"{cls.api_path}/{instance.moneybird_id}")
        except administration.NotFound:
            logging.info(
                f"{cls.entity_type_name} {instance.moneybird_id} not found on Moneybird, was already deleted."
            )

    @classmethod
    def get_from_moneybird(cls, instance):
        if not instance.moneybird_id:
            return None

        administration = get_moneybird_administration()

        logging.info(
            f"Refreshing {cls.entity_type_name} {instance.moneybird_id} from Moneybird"
        )

        data = administration.get(f"{cls.api_path}/{instance.moneybird_id}")

        cls.update_from_moneybird(data, obj=instance)

        instance.update_fields_from_moneybird(data)
        return data

    @classmethod
    def view_on_moneybird_url(cls, obj):
        if not cls.public_path:
            return None
        if not obj.moneybird_id:
            return None
        return f"https://moneybird.com/{settings.MONEYBIRD_ADMINISTRATION_ID}/{cls.public_path}/{obj.moneybird_id}"


class SynchronizableMoneybirdResourceType(MoneybirdResourceType):
    @staticmethod
    def diff_resource_versions(
        old: dict[MoneybirdResourceId, MoneybirdResourceVersion],
        new: dict[MoneybirdResourceId, MoneybirdResourceVersion],
    ) -> ResourceVersionDiff:
        old_ids = old.keys()
        new_ids = new.keys()

        kept = old_ids & new_ids

        diff = ResourceVersionDiff()
        diff.added = list(new_ids - old_ids)
        diff.removed = list(old_ids - new_ids)
        diff.changed = list(
            filter(lambda doc_id: old[doc_id] != new[doc_id], kept)
        )  # Check if the version has changed

        return diff

    @classmethod
    def get_synchronization_api_endpoint(cls):
        return cls.api_path + "/synchronization"

    @classmethod
    def get_local_versions(cls) -> dict[MoneybirdResourceId, MoneybirdResourceVersion]:
        return dict(
            map(
                lambda x: (
                    MoneybirdResourceId(x[0]),
                    MoneybirdResourceVersion(x[1] or 0),
                ),
                cls.get_queryset().values_list("moneybird_id", "moneybird_version"),
            )
        )

    @classmethod
    def get_model_kwargs(cls, data):
        kwargs = super().get_model_kwargs(data)
        version = data.get("version", None)
        if version is not None:
            kwargs["moneybird_version"] = MoneybirdResourceVersion(version)
        return kwargs


class MoneybirdResourceTypeWithDocumentLines(SynchronizableMoneybirdResourceType):
    document_lines_model = None
    document_lines_foreign_key = "document_lines"
    document_foreign_key = "document"
    document_lines_resource_data_name = "details"
    document_lines_attributes_name = "details_attributes"

    @classmethod
    def get_document_line_ids(cls, document) -> list[MoneybirdResourceId]:
        return (
            cls.get_document_lines_queryset(document)
            .exclude(moneybird_id__isnull=True)
            .values_list("moneybird_id", flat=True)
        )

    @classmethod
    def get_local_document_line_versions(cls, document) -> list[MoneybirdResourceId]:
        return list(
            map(
                MoneybirdResourceId,
                cls.get_document_lines_queryset(document)
                .exclude(moneybird_id__isnull=True)
                .values_list("moneybird_id", flat=True),
            )
        )

    @classmethod
    def get_document_lines_queryset(cls, document):
        return getattr(document, cls.document_lines_foreign_key).all()

    @classmethod
    def get_document_line_model_kwargs(cls, line_data: MoneybirdResource, document):
        return {"moneybird_id": MoneybirdResourceId(line_data["id"])}

    @classmethod
    def get_document_line_resource_data(
        cls, data: MoneybirdResource
    ) -> list[MoneybirdResource]:
        return data[cls.document_lines_resource_data_name]

    @staticmethod
    def get_line_with_id(lines, line_id):
        for line in lines:
            if line["id"] == line_id:
                return line
        return None

    @classmethod
    def get_document_line_remote_data_diff(cls, remote_data, local_data):
        diff = []
        for remote_line in remote_data:
            if remote_line["id"] not in [x.get("id", None) for x in local_data]:
                diff.append(
                    {
                        "id": MoneybirdResourceId(remote_line["id"]),
                        "_destroy": True,
                    }
                )
        for local_line in local_data:
            if local_line.get("id", None) is None:
                diff.append(local_line)
            else:
                remote_line = cls.get_line_with_id(remote_data, local_line["id"])
                line_diff = super().get_remote_data_diff(remote_line, local_line)
                line_diff["id"] = MoneybirdResourceId(local_line["id"])
                diff.append(line_diff)
        return diff

    @classmethod
    def get_remote_data_diff(cls, remote_data, local_data):
        document_lines_remote_data = remote_data.pop(cls.document_lines_attributes_name)
        document_lines_local_data = local_data.pop(cls.document_lines_attributes_name)

        diff = super().get_remote_data_diff(remote_data, local_data)

        diff[
            cls.document_lines_attributes_name
        ] = cls.get_document_line_remote_data_diff(
            document_lines_remote_data, document_lines_local_data
        )
        return diff

    @classmethod
    def serialize_for_moneybird(cls, instance):
        data = super().serialize_for_moneybird(instance)
        data.update(cls.serialize_document_lines_for_moneybird(instance))
        return data

    @classmethod
    def serialize_document_line_for_moneybird(cls, document_line, document):
        data = {}
        if document_line.moneybird_id:
            data.update({"id": MoneybirdResourceId(document_line.moneybird_id)})
        return data

    @classmethod
    def _serialize_document_line_for_moneybird(cls, document_line, document):
        if (
            document_line.moneybird_id
            and document_line.should_be_deleted_from_moneybird
        ):
            return {
                "id": MoneybirdResourceId(document_line.moneybird_id),
                "_destroy": True,
            }
        return cls.serialize_document_line_for_moneybird(document_line, document)

    @classmethod
    def serialize_document_lines_for_moneybird(cls, instance):
        return {
            cls.document_lines_attributes_name: list(
                cls._serialize_document_line_for_moneybird(line, instance)
                for line in cls.get_document_lines_queryset(instance)
            )
        }

    @classmethod
    def update_document_lines(cls, document, document_lines_diff: ResourceDiff):
        for document_line in document_lines_diff.added:
            cls.create_document_line_from_moneybird(document, document_line)
        for document_line in document_lines_diff.changed:
            cls.update_document_line_from_moneybird(document, document_line)
        for document_line_id in document_lines_diff.removed:
            cls.delete_document_line_from_moneybird(document, document_line_id)

        cls.get_document_lines_queryset(document).filter(
            moneybird_id__isnull=True
        ).delete()

    @classmethod
    def create_from_moneybird(cls, resource_data: MoneybirdResource):
        document = super().create_from_moneybird(resource_data)
        document_lines = cls.get_document_line_resource_data(resource_data)
        for line_data in document_lines:
            cls.create_document_line_from_moneybird(document, line_data)
        return document

    @classmethod
    def update_from_moneybird(cls, resource_data: MoneybirdResource, obj=None):
        if not resource_data:
            return

        document, created = super().update_from_moneybird(resource_data, obj)
        if document is None:
            logging.warning("No document created for %s", resource_data)
            return
        new_lines = cls.get_document_line_resource_data(resource_data)
        old_lines = cls.get_local_document_line_versions(document)
        document_lines_diff = cls.diff_resources(old_lines, new_lines)
        cls.update_document_lines(document, document_lines_diff)
        return document, created

    @classmethod
    def create_document_line_instance_from_moneybird(
        cls, document, line_data: MoneybirdResource
    ):
        return cls.document_lines_model(
            **cls.get_document_line_model_kwargs(line_data, document)
        )

    @classmethod
    def create_document_line_from_moneybird(
        cls, document, line_data: MoneybirdResource
    ):
        try:
            obj = cls.document_lines_model.objects.get(
                moneybird_id=MoneybirdResourceId(line_data["id"])
            )
        except cls.document_lines_model.DoesNotExist:
            obj = cls.create_document_line_instance_from_moneybird(document, line_data)
            cls.perform_save(obj)
        return obj

    @classmethod
    def update_document_line_from_moneybird(
        cls, document, line_data: MoneybirdResource
    ):
        try:
            obj = cls.get_document_lines_queryset(document).get(
                moneybird_id=MoneybirdResourceId(line_data["id"])
            )
        except cls.model.DoesNotExist:
            return cls.create_document_line_from_moneybird(document, line_data), True

        obj.update_fields_from_moneybird(line_data)
        cls.perform_save(obj)

        return obj, False

    @classmethod
    def delete_document_line_from_moneybird(
        cls, document, resource_id: MoneybirdResourceId
    ):
        return (
            cls.get_document_lines_queryset(document)
            .get(moneybird_id=MoneybirdResourceId(resource_id))
            .delete(delete_on_moneybird=False, received_from_moneybird=True)
        )

    @classmethod
    def reserialize_without_saving(cls, data):
        obj = cls.create_instance_from_moneybird(data)
        document_lines = []
        for line_data in data[cls.document_lines_resource_data_name]:
            document_lines.append(
                cls.create_document_line_instance_from_moneybird(obj, line_data)
            )

        serialized_data = cls.serialize_for_moneybird(obj)
        document_lines_data = [
            cls.serialize_document_line_for_moneybird(document_line, obj)
            for document_line in document_lines
        ]
        serialized_data[cls.document_lines_attributes_name] = document_lines_data
        return serialized_data

    @classmethod
    def push_document_line_to_moneybird(cls, document_line, document, data=None):
        if data is None:
            if document_line.is_synced_with_moneybird:
                return None

            data = cls.serialize_document_line_for_moneybird(document_line, document)

        if not document.moneybird_id:
            document_data = cls.serialize_for_moneybird(document)
            request_data = document_data
            request_data[cls.document_lines_attributes_name] = [data]
        else:
            request_data = {cls.document_lines_attributes_name: [data]}

        if not document_line.moneybird_id:
            old_parent = document.get_from_db()
            old_ids = set(cls.get_document_line_ids(old_parent))

            returned_data = cls.push_to_moneybird(document, request_data)

            current_ids = set(cls.get_document_line_ids(document))
            new_ids = current_ids - old_ids
            if len(new_ids) == 1:
                document_line.pk = new_ids.pop()

        else:
            returned_data = cls.push_to_moneybird(document, request_data)
            document_line.refresh_from_db()

        return returned_data

    @classmethod
    def push_document_line_diff_to_moneybird(cls, document_line):
        document = getattr(document_line, cls.document_foreign_key, None)
        if not document:
            return

        old_instance = document_line.get_from_db()
        if not old_instance:
            return cls.push_document_line_to_moneybird(document_line, document)

        diff = cls.calc_moneybird_data_diff(document_line, old_instance)
        if diff == {}:
            return

        diff.update(
            {"id": MoneybirdResourceId(document_line.moneybird_id)}
        )  # For document lines, the id must always be set

        return cls.push_document_line_to_moneybird(document_line, document, diff)

    @classmethod
    def delete_document_line_on_moneybird(cls, document_line, document):
        if not document_line.moneybird_id:
            return

        document_line_data = {
            "id": MoneybirdResourceId(document_line.moneybird_id),
            "_destroy": True,
        }
        data = {cls.document_lines_attributes_name: [document_line_data]}
        returned_data = cls.push_to_moneybird(document, data)
        cls.perform_save(document)
        return returned_data


def get_moneybird_resources():
    return [
        import_string(resource_type)
        for resource_type in settings.MONEYBIRD_RESOURCE_TYPES
    ]


def get_moneybird_resource_type_for_model(model):
    for resource_type in get_moneybird_resources():
        if resource_type.model == model:
            return resource_type


def get_moneybird_resource_type_for_document_lines_model(model):
    for resource_type in get_moneybird_resources():
        if (
            issubclass(resource_type, MoneybirdResourceTypeWithDocumentLines)
            and resource_type.document_lines_model == model
        ):
            return resource_type


def get_moneybird_resource_type_for_entity(entity_type):
    for resource_type in get_moneybird_resources():
        if resource_type.entity_type == entity_type:
            return resource_type
