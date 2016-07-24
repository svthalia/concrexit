from django.contrib import admin

from documents.models import AssociationDocumentsYear
from documents.models import MiscellaneousDocument
from documents.models import GeneralMeeting, GeneralMeetingDocument


class GeneralMeetingDocInline(admin.StackedInline):
    model = GeneralMeetingDocument


@admin.register(GeneralMeeting)
class GeneralMeetingAdmin(admin.ModelAdmin):
    inlines = (GeneralMeetingDocInline, )


admin.site.register(MiscellaneousDocument)
admin.site.register(AssociationDocumentsYear)
