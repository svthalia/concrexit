from django.db import models, IntegrityError
from django.db.models.utils import resolve_callables
from django.utils.translation import gettext_lazy as _

from moneybird.resource_types import (
    get_moneybird_resource_type_for_model,
    get_moneybird_resource_type_for_document_lines_model,
    MoneybirdResourceType,
)


class MoneybirdResourceModel(models.Model):
    moneybird_id = models.PositiveBigIntegerField(
        verbose_name=_("Moneybird ID"),
        null=True,
        blank=True,
        unique=True,
    )
    _synced_with_moneybird = models.BooleanField(
        default=False,
        verbose_name=_("Synced with Moneybird"),
        help_text=_("Latest changes have been pushed to Moneybird."),
    )
    _delete_from_moneybird = models.BooleanField(
        default=False,
        verbose_name=_("To be deleted from Moneybird"),
        help_text=_("Delete this object from Moneybird when syncing."),
    )

    class Meta:
        abstract = True
        indexes = ["moneybird_id"]

    @property
    def is_synced_with_moneybird(self):
        return self._synced_with_moneybird

    @property
    def should_be_deleted_from_moneybird(self):
        return self._delete_from_moneybird

    @property
    def moneybird_resource_type(self):
        return get_moneybird_resource_type_for_model(self.__class__)

    def serialize_for_moneybird(self):
        if self.moneybird_resource_type is None:
            return None

        return self.moneybird_resource_type.serialize_for_moneybird(self)

    def get_from_db(self):
        if not self.pk:
            return None
        return self.__class__.objects.get(pk=self.pk)

    def update_fields_from_moneybird(self, data):
        if not data:
            return

        fields_to_update = self.moneybird_resource_type.get_model_kwargs(data)
        for k, v in resolve_callables(fields_to_update):
            setattr(self, k, v)

    def push_diff_to_moneybird(self):
        if self.moneybird_resource_type is None:
            return
        self.moneybird_resource_type.push_diff_to_moneybird(self)

    def push_to_moneybird(self, data=None):
        if self.moneybird_resource_type is None:
            return
        self.moneybird_resource_type.push_to_moneybird(self, data)

    def delete_on_moneybird(self):
        if self.moneybird_resource_type is None:
            return
        self.moneybird_resource_type.delete_on_moneybird(self)

    def refresh_from_moneybird(self):
        if self.moneybird_resource_type is None:
            return
        self.moneybird_resource_type.get_from_moneybird(self)

    def save(
        self, push_to_moneybird=False, received_from_moneybird=False, *args, **kwargs
    ):
        if self._synced_with_moneybird and not received_from_moneybird and self.pk:
            old_object = self.__class__.objects.get(pk=self.pk)
            if old_object._synced_with_moneybird:
                diff = MoneybirdResourceType.calc_moneybird_data_diff(self, old_object)
                if diff != {}:
                    self._synced_with_moneybird = False

        if received_from_moneybird:
            self._synced_with_moneybird = True
            self._delete_from_moneybird = False

        if push_to_moneybird:
            if self.moneybird_id is None:
                self.push_to_moneybird()
            else:
                self.push_diff_to_moneybird()

        try:
            return super().save(*args, **kwargs)
        except IntegrityError:
            try:
                existing_obj = self.__class__.objects.get(
                    moneybird_id=self.moneybird_id
                )
                existing_obj.delete(received_from_moneybird=True)
                return super().save(*args, **kwargs)
            except self.__class__.DoesNotExist:
                existing_obj = self.__class__.__base__.objects.get(
                    moneybird_id=self.moneybird_id
                )
                existing_obj.delete(received_from_moneybird=True)
                return super().save(*args, **kwargs)

    def delete(
        self, delete_on_moneybird=False, received_from_moneybird=False, *args, **kwargs
    ):
        if delete_on_moneybird:
            self.delete_on_moneybird()

        if delete_on_moneybird or received_from_moneybird:
            return super().delete(*args, **kwargs)

        self._delete_from_moneybird = True
        self.save(push_to_moneybird=False, received_from_moneybird=False)

    @property
    def moneybird_url(self):
        if self.moneybird_resource_type is None:
            return
        return self.moneybird_resource_type.view_on_moneybird_url(self)


class MoneybirdDocumentLineModel(MoneybirdResourceModel):
    class Meta:
        abstract = True

    @property
    def moneybird_document_line_parent_resource_type_class(self):
        return get_moneybird_resource_type_for_document_lines_model(self.__class__)

    @property
    def document_line_parent(self):
        return getattr(
            self,
            self.moneybird_document_line_parent_resource_type_class.document_foreign_key,
        )

    def serialize_for_moneybird(self):
        if self.document_line_parent is None:
            return None
        return self.moneybird_document_line_parent_resource_type_class.serialize_document_line_for_moneybird(
            self, self.document_line_parent
        )

    def push_diff_to_moneybird(self):
        if self.document_line_parent is None:
            return None
        return self.moneybird_document_line_parent_resource_type_class.push_document_line_diff_to_moneybird(
            self
        )

    def push_to_moneybird(self, data=None):
        if self.document_line_parent is None:
            return None
        return self.moneybird_document_line_parent_resource_type_class.push_document_line_to_moneybird(
            self, self.document_line_parent, data
        )

    def refresh_from_moneybird(self):
        if self.document_line_parent is None:
            return
        return self.document_line_parent.refresh_from_moneybird()

    def save(self, push_to_moneybird=False, *args, **kwargs):
        if push_to_moneybird and self.document_line_parent is not None:
            if self.moneybird_id is None:
                self.push_to_moneybird()  # This will actually save the document line upon receiving the new data from Moneybird
                return
            else:
                self.push_diff_to_moneybird()

        super().save(push_to_moneybird=False, *args, **kwargs)

        if not self._synced_with_moneybird or self._delete_from_moneybird:
            self.document_line_parent._synced_with_moneybird = False
            self.document_line_parent.save()

    def delete(self, delete_on_moneybird=False, *args, **kwargs):
        if delete_on_moneybird:
            self.delete_on_moneybird()
        return super().delete(delete_on_moneybird=False, *args, **kwargs)

    def delete_on_moneybird(self):
        if self.document_line_parent is None:
            return
        self.document_line_parent.moneybird_resource_type.delete_document_line_on_moneybird(
            self, self.document_line_parent
        )

    def update_fields_from_moneybird(self, data):
        fields_to_update = self.moneybird_document_line_parent_resource_type_class.get_document_line_model_kwargs(
            data, self.document_line_parent
        )
        for k, v in resolve_callables(fields_to_update):
            setattr(self, k, v)

    @property
    def moneybird_url(self):
        if self.document_line_parent is None:
            return None
        return self.document_line_parent.moneybird_url

    def get_absolute_url(self):
        return self.moneybird_url


class SynchronizableMoneybirdResourceModel(MoneybirdResourceModel):
    moneybird_version = models.PositiveBigIntegerField(
        verbose_name=_("Moneybird version"), null=True, blank=True
    )

    class Meta:
        abstract = True

    def save(
        self, push_to_moneybird=False, received_from_moneybird=False, *args, **kwargs
    ):
        if self.pk and not received_from_moneybird:
            old_object = self.__class__.objects.get(pk=self.pk)
            if old_object.moneybird_version is not None:
                diff = MoneybirdResourceType.calc_moneybird_data_diff(self, old_object)
                if diff != {}:
                    self.moneybird_version = None
        return super().save(
            push_to_moneybird=push_to_moneybird,
            received_from_moneybird=received_from_moneybird,
            *args,
            **kwargs
        )
