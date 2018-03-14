from django import forms
from django.contrib import admin

from documents.models import (AnnualDocument, AssociationDocument,
                              GeneralMeeting, Minutes,
                              MiscellaneousDocument)
from utils.translation import TranslatedModelAdmin


class MinutesInline(admin.StackedInline):
    model = Minutes
    fields = ('file_nl', 'file_en')


class GeneralMeetingForm(forms.ModelForm):
    class Meta:
        model = GeneralMeeting
        exclude = ()
        widgets = {
            'documents': admin.widgets.FilteredSelectMultiple(
                'documents', is_stacked=False)
        }


@admin.register(GeneralMeeting)
class GeneralMeetingAdmin(TranslatedModelAdmin):
    form = GeneralMeetingForm
    inlines = [
        MinutesInline,
    ]
    list_filter = ('datetime',)


@admin.register(AnnualDocument)
class AnnualDocument(TranslatedModelAdmin):
    fields = ('file', 'subcategory', 'year',)
    list_filter = ('year', 'created', 'last_updated',)


@admin.register(AssociationDocument)
class AssociationDocumentAdmin(TranslatedModelAdmin):
    fields = ('name', 'file', 'members_only',)
    list_filter = ('created', 'last_updated',)


@admin.register(MiscellaneousDocument)
class MiscellaneousDocumentAdmin(TranslatedModelAdmin):
    fields = ('name', 'file', 'members_only',)
    list_filter = ('created', 'last_updated',)
