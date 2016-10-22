from django.contrib import admin

from documents.models import (AssociationDocumentsYear, GeneralMeeting,
                              GeneralMeetingDocument, MiscellaneousDocument)


class GeneralMeetingDocInline(admin.StackedInline):
    model = GeneralMeetingDocument
    classes = ('collapse',)


@admin.register(GeneralMeeting)
class GeneralMeetingAdmin(admin.ModelAdmin):
    inlines = (GeneralMeetingDocInline, )


admin.site.register(MiscellaneousDocument)
admin.site.register(AssociationDocumentsYear)
