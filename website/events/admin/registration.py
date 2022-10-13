"""Registers admin interfaces for the registration model."""
from functools import partial

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.forms import Field
from django.urls import path

import events.admin.views as admin_views
from events import services, models
from .forms import RegistrationAdminForm
from members.models import Member
from payments.widgets import PaymentWidget
from utils.admin import DoNextModelAdmin


@admin.register(models.EventRegistration)
class RegistrationAdmin(DoNextModelAdmin):
    """Custom admin for registrations."""

    form = RegistrationAdminForm

    list_select_related = ["event", "member"]

    def save_model(self, request, obj, form, change):
        if not services.is_organiser(request.member, obj.event):
            raise PermissionDenied
        return super().save_model(request, obj, form, change)

    def has_view_permission(self, request, obj=None):
        """Only give view permission if the user is an organiser."""
        if obj is not None and not services.is_organiser(request.member, obj.event):
            return False
        return super().has_view_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        """Only give change permission if the user is an organiser."""
        if obj is not None and not services.is_organiser(request.member, obj.event):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """Only give delete permission if the user is an organiser."""
        if obj is not None and not services.is_organiser(request.member, obj.event):
            return False
        return super().has_delete_permission(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        return super().get_form(
            request,
            obj,
            formfield_callback=partial(
                self.formfield_for_dbfield, request=request, obj=obj
            ),
            **kwargs,
        )

    def formfield_for_dbfield(self, db_field, request, obj=None, **kwargs):
        """Customise the formfields of event and member."""
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name in ("event", "member"):
            # Disable add/change/delete buttons
            field.widget.can_add_related = False
            field.widget.can_change_related = False
            field.widget.can_delete_related = False
        elif db_field.name == "payment":
            return Field(
                widget=PaymentWidget(obj=obj),
                initial=field.initial,
                required=False,
            )
        return field

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customise the formfields of event and member."""
        if db_field.name == "event":
            # allow to restrict event
            if request.GET.get("event_pk"):
                kwargs["queryset"] = models.Event.objects.filter(
                    pk=int(request.GET["event_pk"])
                )
            else:
                kwargs["queryset"] = models.Event.objects
            # restrict to events organised by user
            if not (
                request.user.is_superuser
                or request.user.has_perm("events.override_organiser")
            ):
                kwargs["queryset"] = kwargs["queryset"].filter(
                    organisers__in=list(
                        request.member.get_member_groups().values_list("id", flat=True)
                    )
                )
        elif db_field.name == "member":
            # Filter the queryset to current members only
            kwargs["queryset"] = Member.current_members.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:registration>/fields/",
                self.admin_site.admin_view(
                    admin_views.RegistrationAdminFields.as_view(admin=self)
                ),
                name="events_registration_fields",
            ),
        ]
        return custom_urls + urls
