"""The forms defined by the documents package"""
from django import forms
from django.contrib import admin

from documents.models import GeneralMeeting


class GeneralMeetingForm(forms.ModelForm):
    """Custom form for general meetings with a custom widget for documents"""
    class Meta:
        model = GeneralMeeting
        exclude = ()
        widgets = {
            'documents': admin.widgets.FilteredSelectMultiple(
                'documents', is_stacked=False)
        }
