"""The forms defined by the documents package"""
from django import forms
from django.contrib import admin
from django.utils import timezone

from documents.models import AnnualDocument, GeneralMeeting
from utils.snippets import datetime_to_lectureyear


class AnnualDocumentForm(forms.ModelForm):
    class Meta:
        model = AnnualDocument
        exclude = ()
        widgets = {
            'year': forms.Select
        }

    def current_year():
        return datetime_to_lectureyear(timezone.now())

    def year_choices():
        current = datetime_to_lectureyear(timezone.now())
        return [
            (year, "{}-{}".format(year, year+1))
            for year in range(current + 1, 1989, -1)
        ]

    year = forms.TypedChoiceField(coerce=int, choices=year_choices,
                                  initial=current_year)


class GeneralMeetingForm(forms.ModelForm):
    """Custom form for general meetings with a custom widget for documents"""
    class Meta:
        model = GeneralMeeting
        exclude = ()
        widgets = {
            'documents': admin.widgets.FilteredSelectMultiple(
                'documents', is_stacked=False)
        }
