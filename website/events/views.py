from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required

from .models import Event


@staff_member_required
@permission_required('events.change_event')
def admin_details(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    n = event.max_participants
    registrations = list(event.registration_set.filter(date_cancelled=None))
    cancellations = event.registration_set.exclude(date_cancelled=None)
    return render(request, 'events/admin/details.html', {
        'event': event,
        'registrations': registrations[:n],
        'waiting': registrations[n:] if n else [],
        'cancellations': cancellations,
    })
