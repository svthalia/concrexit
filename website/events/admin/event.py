"""Registers admin interfaces for the event model."""

from django.contrib import admin
from django.template.defaultfilters import date as _date
from django.urls import reverse, path
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from activemembers.models import MemberGroup
from events import services
from events import models
from events.admin.filters import LectureYearFilter
from events.admin.forms import RegistrationInformationFieldForm
from events.admin.inlines import (
    RegistrationInformationFieldInline,
    PizzaEventInline,
    PromotionRequestInline,
)
from events.admin.views import (
    EventAdminDetails,
    EventRegistrationsExport,
    EventMessage,
    EventMarkPresentQR,
)
from utils.admin import DoNextModelAdmin


@admin.register(models.Event)
class EventAdmin(DoNextModelAdmin):
    """Manage the events."""

    inlines = (
        RegistrationInformationFieldInline,
        PizzaEventInline,
        PromotionRequestInline,
    )
    list_display = (
        "overview_link",
        "event_date",
        "registration_date",
        "num_participants",
        "organiser",
        "category",
        "published",
        "edit_link",
    )
    list_display_links = ("edit_link",)
    list_filter = (LectureYearFilter, "start", "published", "category")
    actions = ("make_published", "make_unpublished")
    date_hierarchy = "start"
    search_fields = ("title", "description")
    prepopulated_fields = {"map_location": ("location",)}
    filter_horizontal = ("documents",)

    fieldsets = (
        (
            _("General"),
            {
                "fields": (
                    "title",
                    "published",
                    "organiser",
                )
            },
        ),
        (
            _("Detail"),
            {
                "fields": (
                    "category",
                    "start",
                    "end",
                    "description",
                    "caption",
                    "location",
                    "map_location",
                ),
                "classes": ("collapse", "start-open"),
            },
        ),
        (
            _("Registrations"),
            {
                "fields": (
                    "price",
                    "fine",
                    "tpay_allowed",
                    "max_participants",
                    "registration_start",
                    "registration_end",
                    "cancel_deadline",
                    "send_cancel_email",
                    "optional_registrations",
                    "no_registration_message",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Extra"),
            {"fields": ("slide", "documents", "shift"), "classes": ("collapse",)},
        ),
    )

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
        form.clean = lambda form: form.instance.clean_changes(form.changed_data)
        return form

    def overview_link(self, obj):
        return format_html(
            '<a href="{link}">{title}</a>',
            link=reverse("admin:events_event_details", kwargs={"pk": obj.pk}),
            title=obj.title,
        )

    def has_change_permission(self, request, obj=None):
        """Only allow access to the change form if the user is an organiser."""
        if obj is not None and not services.is_organiser(request.member, obj):
            return False
        return super().has_change_permission(request, obj)

    def event_date(self, obj):
        event_date = timezone.make_naive(obj.start)
        return _date(event_date, "l d b Y, G:i")

    event_date.short_description = _("Event Date")
    event_date.admin_order_field = "start"

    def registration_date(self, obj):
        if obj.registration_start is not None:
            start_date = timezone.make_naive(obj.registration_start)
        else:
            start_date = obj.registration_start

        return _date(start_date, "l d b Y, G:i")

    registration_date.short_description = _("Registration Start")
    registration_date.admin_order_field = "registration_start"

    def edit_link(self, obj):
        return _("Edit")

    edit_link.short_description = ""

    def num_participants(self, obj):
        """Pretty-print the number of participants."""
        num = obj.eventregistration_set.exclude(
            date_cancelled__lt=timezone.now()
        ).count()
        if not obj.max_participants:
            return f"{num}/∞"
        return f"{num}/{obj.max_participants}"

    num_participants.short_description = _("Number of participants")

    def make_published(self, request, queryset):
        """Change the status of the event to published."""
        self._change_published(request, queryset, True)

    make_published.short_description = _("Publish selected events")

    def make_unpublished(self, request, queryset):
        """Change the status of the event to unpublished."""
        self._change_published(request, queryset, False)

    make_unpublished.short_description = _("Unpublish selected events")

    @staticmethod
    def _change_published(request, queryset, published):
        if not request.user.is_superuser:
            queryset = queryset.filter(organiser__in=request.member.get_member_groups())
        queryset.update(published=published)

    def save_formset(self, request, form, formset, change):
        """Save formsets with their order."""
        formset.save()

        informationfield_forms = (
            x
            for x in formset.forms
            if isinstance(x, RegistrationInformationFieldForm)
            and "DELETE" not in x.changed_data
        )
        form.instance.set_registrationinformationfield_order(
            [
                f.instance.pk
                for f in sorted(
                    informationfield_forms,
                    key=lambda x: (x.cleaned_data["order"], x.instance.pk),
                )
            ]
        )
        form.instance.save()

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Customise formfield for organiser."""
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "organiser":
            # Disable add/change/delete buttons
            field.widget.can_add_related = False
            field.widget.can_change_related = False
            field.widget.can_delete_related = False
        return field

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customise the organiser formfield, limit the options."""
        if db_field.name == "organiser":
            # Use custom queryset for organiser field
            # Only get the current active committees the user is a member of
            if not (
                request.user.is_superuser
                or request.user.has_perm("events.override_organiser")
            ):
                kwargs["queryset"] = request.member.get_member_groups()
            else:
                # Hide old boards and inactive committees for new events
                if "add" in request.path:
                    kwargs[
                        "queryset"
                    ] = MemberGroup.active_objects.all() | MemberGroup.objects.filter(
                        board=None
                    ).exclude(
                        until__lt=(timezone.now() - timezone.timedelta(weeks=1))
                    )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def get_formsets_with_inlines(self, request, obj=None):
        for inline in self.get_inline_instances(request, obj):
            if self.has_change_permission(request, obj) or obj is None:
                yield inline.get_formset(request, obj), inline

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:pk>/details/",
                self.admin_site.admin_view(EventAdminDetails.as_view()),
                name="events_event_details",
            ),
            path(
                "<int:pk>/export/",
                self.admin_site.admin_view(EventRegistrationsExport.as_view()),
                name="events_event_export",
            ),
            path(
                "<int:pk>/message/",
                self.admin_site.admin_view(EventMessage.as_view(admin=self)),
                name="events_event_message",
            ),
            path(
                "<int:pk>/mark-present-qr/",
                self.admin_site.admin_view(EventMarkPresentQR.as_view()),
                name="events_event_mark_present_qr",
            ),
        ]
        return custom_urls + urls
