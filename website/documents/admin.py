from django.contrib import admin

from documents.models import AssociationDocument
from documents.models import GenericDocument
from documents.models import GeneralMeeting, GeneralMeetingDocument


class GeneralMeetingDocInline(admin.StackedInline):
    model = GeneralMeetingDocument


@admin.register(GeneralMeeting)
class GeneralMeetingAdmin(admin.ModelAdmin):
    inlines = (GeneralMeetingDocInline, )


admin.site.register(GenericDocument)
admin.site.register(AssociationDocument)
