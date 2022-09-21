"""Registers admin interfaces for the event model."""

from django.contrib import admin
from django.db.models import Count, Q
from django.template.defaultfilters import date as _date
from django.urls import reverse, path, resolve
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from activemembers.models import MemberGroup
from events import services
from events import models
from events.admin.filters import LectureYearFilter
from events.admin.forms import RegistrationInformationFieldForm, EventAdminForm
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

    form = EventAdminForm

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
    filter_horizontal = ("documents", "organisers")

    fieldsets = (
        (
            _("General"),
            {
                "fields": (
                    "title",
                    "published",
                    "organisers",
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

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                participant_count=Count(
                    "eventregistration",
                    filter=~Q(eventregistration__date_cancelled__lt=timezone.now()),
                )
            )
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
        num = obj.participant_count  # from annotation
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
            queryset = queryset.filter(
                organisers__in=request.member.get_member_groups()
            )
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

    def get_field_queryset(self, db, db_field, request):
        """Members without the can view as organiser permission can only assign their own groups as organiser."""
        pk = resolve(request.path_info).kwargs["object_id"]
        if db_field.name == "organisers" and not request.user.has_perm(
            "events.override_organiser"
        ):
            return request.member.get_member_groups().union(
                MemberGroup.objects.filter(event_organiser__pk=pk)
            )
        return super().get_field_queryset(db, db_field, request)
