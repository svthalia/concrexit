from django.contrib import admin

from events.forms import EventDocumentForm
from events.models.documents import EventDocument
from events.services import is_eventdocument_owner


@admin.register(EventDocument)
class EventDocumentAdmin(admin.ModelAdmin):
    """Manage the event documents."""

    form = EventDocumentForm
    list_filter = (
        "created",
        "last_updated",
        "members_only",
    )
    list_display = (
        "__str__",
        "members_only",
    )

    def has_change_permission(self, request, obj=None):
        """Only allow access to the change form if the user is an owner."""
        if obj is not None and not is_eventdocument_owner(request.member, obj):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """Only allow delete access if the user is an owner."""
        if obj is not None and not is_eventdocument_owner(request.member, obj):
            return False
        return super().has_delete_permission(request, obj)
