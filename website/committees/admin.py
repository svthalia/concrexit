from django.contrib import admin

from . import models


@admin.register(models.Committee)
class CommitteeAdmin(admin.ModelAdmin):
    list_filter = ('until',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(board__is_board=True)


@admin.register(models.Board)
class BoardAdmin(admin.ModelAdmin):
    exclude = ('is_board',)


@admin.register(models.CommitteeMembership)
class CommitteeMembershipAdmin(admin.ModelAdmin):
    pass
