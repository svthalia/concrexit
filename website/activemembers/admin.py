from django.contrib import admin
from utils.translation import TranslatedModelAdmin

from . import models

@admin.register(models.Committee)
class CommitteeAdmin(TranslatedModelAdmin):
    list_filter = ('until',)

    fieldsets = (
        (None, {
            'fields': (
                'name', 'description', 'photo', 'permissions',
                'since', 'until'
            )
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(board__is_board=True)


@admin.register(models.Board)
class BoardAdmin(TranslatedModelAdmin):
    exclude = ('is_board',)


@admin.register(models.CommitteeMembership)
class CommitteeMembershipAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Mentorship)
class MentorsAdmin(admin.ModelAdmin):
    pass
