from import_export import resources
from import_export.fields import Field

from events.models import Event


class EventResource(resources.ModelResource):
    name = Field(attribute="name", column_name="name")
    email = Field(attribute="email", column_name="email")
    paid = Field(attribute="paid", column_name="paid")
    present = Field(attribute="present", column_name="present")
    status = Field(attribute="status", column_name="status")
    phone_number = Field(attribute="phone_number", column_name="phone_number")
    date = Field(attribute="date", column_name="date")
    date_cancelled = Field(attribute="date_cancelled", column_name="date_cancelled")

    # optional filtering to allow exporting a single event
    # like with the button in the detail page of an event
    def get_queryset(self, pk=None):
        if pk is not None:
            return Event.objects.filter(pk=pk)
        return Event.objects

    class Meta:
        model = Event
        fields = (
            "name",
            "email",
            "paid",
            "present",
            "status",
            "phone_number",
            "date",
            "date_cancelled",
        )
        export_order = fields
