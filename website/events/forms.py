from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import get_language

from .models import RegistrationInformationField


class RegistrationInformationFieldForm(forms.ModelForm):
    order = forms.IntegerField(label=_('order'), initial=0)

    class Meta:
        fields = '__all__'
        model = RegistrationInformationField
        widgets = {
            'type': forms.Select,
        }


class FieldsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        registration = kwargs.pop('registration')
        super(FieldsForm, self).__init__(*args, **kwargs)

        self.information_fields = registration.registration_information()

        for information_field in self.information_fields:
            field = information_field['field']
            key = "info_field_{}".format(field.id)

            if field.type == RegistrationInformationField.BOOLEAN_FIELD:
                self.fields[key] = forms.BooleanField(
                    required=False
                )
            elif field.type == RegistrationInformationField.INTEGER_FIELD:
                self.fields[key] = forms.IntegerField()
            elif field.type == RegistrationInformationField.TEXT_FIELD:
                self.fields[key] = forms.CharField()

            self.fields[key].label = getattr(field, '{}_{}'.format(
                'name', get_language()))
            self.fields[key].help_text = getattr(field, '{}_{}'.format(
                'description', get_language()))
            self.fields[key].initial = information_field['value']
            if not field.type == RegistrationInformationField.BOOLEAN_FIELD:
                self.fields[key].required = field.required

    def field_values(self):
        for information_field in self.information_fields:
            key = "info_field_{}".format(information_field['field'].id)
            field = {
                "field": information_field["field"],
                "value": self.cleaned_data[key]
            }
            yield field
