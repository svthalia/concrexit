"""Registers admin interfaces for the models defined in this module."""

from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.db import models
from django.db.models.functions import Lower

from events.services import is_organiser
from promotion.forms import PromotionRequestForm

from .models import PromotionChannel, PromotionRequest


class CaseInsensitiveFilter(admin.FieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_kwarg = f"{field_path}__iexact"
        self.lookup_kwarg2 = f"{field_path}__isnull"
        self.lookup_val = params.get(self.lookup_kwarg)
        self.lookup_val2 = params.get(self.lookup_kwarg2)
        super().__init__(field, request, params, model, model_admin, field_path)
        self.empty_value_display = model_admin.get_empty_value_display()
        queryset = model_admin.get_queryset(request)
        lookup_choices = (
            queryset.annotate(lowered=Lower(field.name))
            .order_by(field.name)
            .distinct()
            .values_list(field.name, flat=True)
        )
        self.lookup_choices = set(
            map(lambda x: x.lower() if x is not None else x, lookup_choices)
        )

    def get_facet_counts(self, pk_attname, filtered_qs):
        return {
            f"{i}__c": models.Count(
                pk_attname,
                filter=models.Q(
                    (self.lookup_kwarg, value)
                    if value is not None
                    else (self.lookup_kwarg2, True)
                ),
            )
            for i, value in enumerate(self.lookup_choices)
        }

    def choices(self, changelist):
        add_facets = changelist.add_facets
        facet_counts = self.get_facet_queryset(changelist)
        yield {
            "selected": self.lookup_val is None,
            "query_string": changelist.get_query_string(
                remove=[self.lookup_kwarg, self.lookup_kwarg2]
            ),
            "display": "All",
        }
        include_none = False
        empty_title = self.empty_value_display
        for key, val in enumerate(self.lookup_choices):
            if add_facets:
                count = facet_counts[f"{key}__c"]
            if val is None:
                include_none = True
                empty_title = f"{empty_title} ({count})" if add_facets else empty_title
                continue
            yield {
                "selected": self.lookup_val is not None and val in self.lookup_val,
                "query_string": changelist.get_query_string({self.lookup_kwarg: val}),
                "display": f"{val} ({count})" if add_facets else val,
            }
        if include_none:
            yield {
                "selected": self.lookup_val2 is True,
                "query_string": changelist.get_query_string(
                    {self.lookup_kwarg2: "True"}, remove=[self.lookup_kwarg]
                ),
                "display": empty_title,
            }

    def expected_parameters(self):
        return [self.lookup_kwarg, self.lookup_kwarg2]


@admin.register(PromotionRequest)
class PromotionRequestAdmin(admin.ModelAdmin):
    """This manages the admin interface for the model items."""

    list_display = ("event", "publish_date", "channel", "assigned_to", "status")
    list_filter = (
        "publish_date",
        ("assigned_to", CaseInsensitiveFilter),
        "status",
    )
    date_hierarchy = "publish_date"
    form = PromotionRequestForm
    actions = ["mark_not_started", "mark_started", "mark_finished", "mark_published"]

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.event and is_organiser(request.member, obj.event):
            return True
        return super().has_change_permission(request, obj)

    def mark_not_started(self, request, queryset):
        """Change the status of the event to published."""
        self._change_published(queryset, PromotionRequest.NOT_STARTED)

    mark_not_started.short_description = "Mark requests as not started"

    def mark_started(self, request, queryset):
        """Change the status of the event to published."""
        self._change_published(queryset, PromotionRequest.STARTED)

    mark_started.short_description = "Mark requests as started"

    def mark_finished(self, request, queryset):
        """Change the status of the event to published."""
        self._change_published(queryset, PromotionRequest.FINISHED)

    mark_finished.short_description = "Mark requests as finished"

    def mark_published(self, request, queryset):
        """Change the status of the event to published."""
        self._change_published(queryset, PromotionRequest.PUBLISHED)

    mark_published.short_description = "Mark requests as published"

    @staticmethod
    def _change_published(queryset, status):
        queryset.update(status=status)


@admin.register(PromotionChannel)
class PromotionChannelAdmin(ModelAdmin):
    list_display = ("name", "publisher_reminder_email")
