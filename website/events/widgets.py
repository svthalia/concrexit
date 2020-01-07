"""Widgets provided by the payments package"""
from django.forms import Widget


class FieldsWidget(Widget):
    """
    Custom widget for linking to the fields, used in registrations
    """

    template_name = "events/admin/fields_widget.html"

    def value_from_datadict(self, data, files, name):
        return super().value_from_datadict(data, files, name)
