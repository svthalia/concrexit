from django import forms
from django.utils.translation import gettext_lazy as _

from documents.forms import DocumentFileInput
from events.models.documents import EventDocument

from .models import RegistrationInformationField


class FieldsForm(forms.Form):
    """Form that outputs the correct widgets for the information fields."""

    def __init__(self, *args, **kwargs):
        self.information_fields = kwargs.pop("fields")
        super().__init__(*args, **kwargs)

        for key, field in self.information_fields.items():
            field_type = field["type"]

            if field_type == RegistrationInformationField.BOOLEAN_FIELD:
                self.fields[key] = forms.BooleanField(required=False)
            elif field_type == RegistrationInformationField.INTEGER_FIELD:
                self.fields[key] = forms.IntegerField(required=field["required"])
            elif field_type == RegistrationInformationField.TEXT_FIELD:
                self.fields[key] = forms.CharField(required=field["required"])

            self.fields[key].label = field["label"]
            self.fields[key].help_text = field["description"]
            self.fields[key].initial = field["value"]

    def field_values(self):
        for key in self.information_fields:
            yield key, self.cleaned_data[key]


class EventDocumentForm(forms.ModelForm):
    """Form that overrides the widgets for the files."""

    class Meta:
        model = EventDocument
        fields = (
            "name",
            "file",
            "members_only",
            "owner",
        )
        widgets = {
            "file": DocumentFileInput,
        }
