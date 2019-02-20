"""Registers admin interfaces for the payments module"""
import csv

from django.contrib import admin, messages
from django.contrib.admin.utils import model_ngettext
from django.http import HttpResponse
from django.urls import path
from django.utils.html import format_html
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _

from payments import services, admin_views
from .models import Payment


def _show_message(admin, request, n, message, error):
    if n == 0:
        admin.message_user(request, error, messages.ERROR)
    else:
        admin.message_user(request, message % {
            "count": n,
            "items": model_ngettext(admin.opts, n)
        }, messages.SUCCESS)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Manage the payments"""

    list_display = ('created_at', 'amount',  'processing_date', 'type',
                    'paid_by_link', 'processed_by_link', 'notes')
    list_filter = ('type',)
    list_select_related = ('paid_by', 'processed_by',)
    date_hierarchy = 'created_at'
    fields = ('created_at', 'amount', 'type', 'processing_date',
              'paid_by', 'processed_by', 'notes')
    readonly_fields = ('created_at', 'amount', 'type',
                       'processing_date', 'paid_by', 'processed_by',
                       'notes')
    search_fields = ('notes', 'paid_by__username', 'paid_by__first_name',
                     'paid_by__last_name', 'processed_by__username',
                     'processed_by__first_name', 'processed_by__last_name',
                     'amount')
    ordering = ('-created_at', 'processing_date')
    autocomplete_fields = ('paid_by', 'processed_by')
    actions = ['process_cash_selected', 'process_card_selected',
               'process_wire_selected', 'export_csv']

    @staticmethod
    def _member_link(member):
        if member:
            return format_html("<a href='{}'>{}</a>",
                               member.get_absolute_url(),
                               member.get_full_name())
        else:
            return "-"

    def paid_by_link(self, obj):
        return self._member_link(obj.paid_by)
    paid_by_link.admin_order_field = 'paid_by'
    paid_by_link.short_description = _('paid by')

    def processed_by_link(self, obj):
        return self._member_link(obj.processed_by)
    processed_by_link.admin_order_field = 'processed_by'
    processed_by_link.short_description = _('processed by')

    def changeform_view(self, request, object_id=None, form_url='',
                        extra_context=None):
        """
        Renders the change formview
        Only allow when the payment has not been processed yet
        """
        obj = None
        if (object_id is not None and
                request.user.has_perm('payments.process_payments')):
            obj = Payment.objects.get(id=object_id)
            if obj.processed:
                obj = None
        return super().changeform_view(
            request, object_id, form_url, {'payment': obj})

    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return 'created_at', 'type', 'processing_date', 'processed_by'
        return super().get_readonly_fields(request, obj)

    def get_actions(self, request):
        """Get the actions for the payments"""
        """Hide the processing actions if the right permissions are missing"""
        actions = super().get_actions(request)
        if not request.user.has_perm('payments.process_payments'):
            del(actions['process_cash_selected'])
            del(actions['process_card_selected'])
            del(actions['process_wire_selected'])
        return actions

    def process_cash_selected(self, request, queryset):
        """Process the selected payment as cash"""
        if request.user.has_perm('payments.process_payments'):
            updated_payments = services.process_payment(
                queryset, request.member, Payment.CASH
            )
            self._process_feedback(request, updated_payments)
    process_cash_selected.short_description = _(
        'Process selected payments (cash)')

    def process_card_selected(self, request, queryset):
        """Process the selected payment as card"""
        if request.user.has_perm('payments.process_payments'):
            updated_payments = services.process_payment(
                queryset, request.member, Payment.CARD
            )
            self._process_feedback(request, updated_payments)
    process_card_selected.short_description = _(
        'Process selected payments (card)')

    def process_wire_selected(self, request, queryset):
        """Process the selected payment as wire"""
        if request.user.has_perm('payments.process_payments'):
            updated_payments = services.process_payment(
                queryset, request.member, Payment.WIRE
            )
            self._process_feedback(request, updated_payments)
    process_wire_selected.short_description = _(
        'Process selected payments (wire)')

    def _process_feedback(self, request, updated_payments):
        """Show a feedback message for the processing result"""
        rows_updated = len(updated_payments)
        _show_message(
            self, request, rows_updated,
            message=_("Successfully processed %(count)d %(items)s."),
            error=_('The selected payment(s) could not be processed.')
        )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<uuid:pk>/process/',
                 self.admin_site.admin_view(
                     admin_views.PaymentAdminView.as_view()),
                 name='payments_payment_process'),
        ]
        return custom_urls + urls

    def export_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment;\
                                           filename="payments.csv"'
        writer = csv.writer(response)
        headers = [_('created'), _('processed'), _('amount'), _('type'),
                   _('processor'), _('payer id'), _('payer name'),
                   _('notes')]
        writer.writerow([capfirst(x) for x in headers])
        for payment in queryset:
            writer.writerow([
                payment.created_at,
                payment.processing_date,
                payment.amount,
                payment.get_type_display(),
                payment.processed_by.get_full_name()
                if payment.processed_by else '-',
                payment.paid_by.pk
                if payment.paid_by else '-',
                payment.paid_by.get_full_name()
                if payment.paid_by else '-',
                payment.notes
            ])
        return response
    export_csv.short_description = _('Export')
