from django.forms import Widget


class FieldsWidget(Widget):
    """Custom widget for linking to the fields, used in registrations."""

    template_name = "events/admin/fields_widget.html"
