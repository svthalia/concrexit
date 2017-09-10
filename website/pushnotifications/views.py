from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, redirect

from pushnotifications.models import Message


@staff_member_required
@permission_required('pushnotifications.change_message')
def admin_send(request, pk):
    message = get_object_or_404(Message, pk=pk)
    message.send()
    return redirect('admin:pushnotifications_message_changelist')
