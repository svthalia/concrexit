from django.contrib import admin

from activemembers.forms import CommitteeMembershipForm
from utils.translation import TranslatedModelAdmin
from . import models


class CommitteeMembershipInline(admin.StackedInline):
    model = models.CommitteeMembership
    can_delete = False
    ordering = ('since',)
    extra = 0


@admin.register(models.Committee)
class CommitteeAdmin(TranslatedModelAdmin):
    inlines = (CommitteeMembershipInline,)
    list_filter = ('until',)
    search_fields = ('name', 'description')

    fields = ('name', 'description', 'photo', 'permissions',
              'since', 'until', 'contact_email', 'wiki_namespace', 'active')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(board__is_board=True)


@admin.register(models.Board)
class BoardAdmin(TranslatedModelAdmin):
    inlines = (CommitteeMembershipInline,)
    exclude = ('is_board',)

    fields = ('name', 'photo', 'permissions',
              'since', 'until',)


@admin.register(models.CommitteeMembership)
class CommitteeMembershipAdmin(TranslatedModelAdmin):
    form = CommitteeMembershipForm
    list_display = ('member', 'committee', 'since', 'until', 'chair', 'role')
    list_filter = ('committee',)
    search_fields = ('member__user__first_name', 'member__user__last_name',
                     'member__user__email')


@admin.register(models.Mentorship)
class MentorsAdmin(admin.ModelAdmin):
    pass
