"""The forms defined by the documents package."""
from django import forms
from django.contrib import admin
from django.forms import widgets
from django.utils import timezone

from documents import models
from utils.snippets import datetime_to_lectureyear


class DocumentFileInput(widgets.ClearableFileInput):
    """Wrapper around Django's :class:`~django.forms.widgets.ClearableFileInput`.

    It overrides the URL of the associated file when it is fetched.
    """

    template_name = "widgets/clearable_file_input.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if hasattr(value, "url"):
            doc = models.Document.objects.get(file=value)
            context["document_id"] = doc.pk
            context["language"] = "en"
        return context


class MinutesForm(forms.ModelForm):
    """Form that overrides the widgets for the files."""

    class Meta:
        model = models.Minutes
        fields = (
            "file",
            "members_only",
        )
        widgets = {
            "file": DocumentFileInput,
        }


class AnnualDocumentForm(forms.ModelForm):
    """Form that provides custom functionality for annual documents."""

    class Meta:
        model = models.AnnualDocument
        fields = "__all__"
        widgets = {
            "year": forms.Select,
            "file": DocumentFileInput,
        }

    @staticmethod
    def _current_year():
        """Get the current lecture year."""
        return datetime_to_lectureyear(timezone.now())

    @staticmethod
    def _year_choices():
        """Get the lecture years."""
        current = datetime_to_lectureyear(timezone.now())
        return [(year, f"{year}-{year + 1}") for year in range(current + 1, 1989, -1)]

    year = forms.TypedChoiceField(
        coerce=int, choices=_year_choices.__func__, initial=_current_year.__func__
    )


class AssociationDocumentForm(forms.ModelForm):
    """Form that overrides the widgets for the files."""

    class Meta:
        model = models.AssociationDocument
        fields = (
            "name",
            "file",
            "members_only",
        )
        widgets = {
            "file": DocumentFileInput,
        }


class MiscellaneousDocumentForm(forms.ModelForm):
    """Form that overrides the widgets for the files."""

    class Meta:
        model = models.MiscellaneousDocument
        fields = (
            "name",
            "file",
            "members_only",
        )
        widgets = {
            "file": DocumentFileInput,
        }


class GeneralMeetingForm(forms.ModelForm):
    """Custom form for general meetings with a custom widget for documents."""

    class Meta:
        model = models.GeneralMeeting
        fields = "__all__"
        widgets = {
            "documents": admin.widgets.FilteredSelectMultiple(
                "documents", is_stacked=False
            )
        }
