from django.contrib import admin, messages
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _, ngettext

from moneybird.models import (
    SynchronizableMoneybirdResourceModel,
    MoneybirdDocumentLineModel,
)
from moneybird.resource_types import (
    get_moneybird_resource_type_for_model,
    get_moneybird_resource_type_for_document_lines_model,
)
from moneybird.settings import settings


def push_to_moneybird(admin_obj, request, queryset):
    qs = queryset.filter(_synced_with_moneybird=False)
    errors = 0
    for obj in qs:
        try:
            admin_obj.push_to_moneybird()
        except Exception as e:
            admin_obj.message_user(
                request,
                _("Error pushing %s to Moneybird: %s") % (obj, e),
                messages.ERROR,
            )
            errors += 1

    successful = qs.count() - errors

    if successful >= 1:
        admin_obj.message_user(
            request,
            ngettext(
                "%d object was successfully pushed to Moneybird.",
                "%d objects were successfully pushed to Moneybird.",
                successful,
            )
            % successful,
            messages.SUCCESS,
        )


class MoneybirdResourceModelAdminMixin:
    has_non_moneybird_fields = False

    def get_queryset(self, *args, **kwargs):
        return (
            super().get_queryset(*args, **kwargs).filter(_delete_from_moneybird=False)
        )

    @property
    def moneybird_resource_type(self):
        if issubclass(self.model, MoneybirdDocumentLineModel):
            return get_moneybird_resource_type_for_document_lines_model(self.model)
        return get_moneybird_resource_type_for_model(self.model)

    def get_readonly_fields(self, *args, **kwargs):
        readonly_fields = (
            "moneybird_id",
            "_synced_with_moneybird",
            "_delete_from_moneybird",
        )
        if issubclass(self.model, SynchronizableMoneybirdResourceModel):
            readonly_fields += ("moneybird_version",)
        return tuple(super().get_readonly_fields(*args, **kwargs)) + readonly_fields

    def has_delete_permission(self, *args, **kwargs):
        resource_type = self.moneybird_resource_type
        if resource_type and not resource_type.can_delete:
            return False
        return super().has_delete_permission(*args, **kwargs)

    def has_add_permission(self, *args, **kwargs):
        resource_type = self.moneybird_resource_type
        if resource_type and not resource_type.can_write:
            return False
        return super().has_delete_permission(*args, **kwargs)

    def has_change_permission(self, *args, **kwargs):
        resource_type = self.moneybird_resource_type
        if (
            resource_type
            and not resource_type.can_write
            and not self.has_non_moneybird_fields
        ):
            return False
        return super().has_change_permission(*args, **kwargs)

    @admin.display(description="View on Moneybird")
    def view_on_moneybird(self, obj):
        url = obj.moneybird_url
        if url is None:
            return None
        return mark_safe(
            f'<a class="button small" href="{url}" target="_blank" style="white-space: nowrap;">View on Moneybird</a>'
        )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if settings.MONEYBIRD_AUTO_PUSH:
            obj = form.instance
            try:
                obj.push_to_moneybird()
            except Exception as e:
                self.message_user(
                    request, _("Error pushing to Moneybird: %s") % e, messages.ERROR
                )

    def delete_model(self, request, obj):
        if settings.MONEYBIRD_AUTO_PUSH:
            obj.delete(delete_on_moneybird=True)
        else:
            return super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """Given a queryset, delete it from the database."""
        if settings.MONEYBIRD_AUTO_PUSH:
            for obj in queryset:
                obj.delete(delete_on_moneybird=True)
        else:
            self.moneybird_resource_type.queryset_delete(queryset)


class MoneybirdResourceModelAdmin(MoneybirdResourceModelAdminMixin, admin.ModelAdmin):
    pass
