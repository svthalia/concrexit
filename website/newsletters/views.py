"""Views provided by the newsletters package"""
from datetime import datetime, timedelta, date

import os

from django.conf import settings

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import activate, get_language_info

from events.models import Event
from newsletters import emails
from newsletters.models import Newsletter
from partners.models import Partner

from sendfile import sendfile


def preview(request, pk, lang=None):
    """
    View that renders the newsletter as HTML

    :param request: the request object
    :param pk: the newsletter's primary key
    :param lang: the language of the render
    :return: HttpResponse 200 containing the newsletter HTML
    """
    lang_code = request.LANGUAGE_CODE

    if lang is not None:
        try:
            get_language_info(lang)
            activate(lang)
            lang_code = lang
        except KeyError:
            # Language code not recognised by get_language_info
            pass

    # Send cached file, if it exists
    file_path = os.path.join(
        settings.MEDIA_ROOT,
        'newsletters',
        f'{pk}_{lang_code}.html'
    )
    if os.path.isfile(file_path):
        return sendfile(request, file_path)

    newsletter = get_object_or_404(Newsletter, pk=pk)
    partners = Partner.objects.filter(is_main_partner=True)
    main_partner = partners[0] if len(partners) > 0 else None
    events = None

    if newsletter.date:
        start_date = newsletter.date
        end_date = start_date + timezone.timedelta(weeks=1)
        events = Event.objects.filter(
            start__gte=start_date, end__lt=end_date).order_by('start')

    return render(request, 'newsletters/email.html', {
        'newsletter': newsletter,
        'agenda_events': events,
        'main_partner': main_partner,
        'lang_code': lang_code
    })


def legacy_redirect(request, year, week):
    """
    View that redirect you to the right newsletter by
    using the previously used URL format of /{year}/{week}

    :param request: the request object
    :param year: the year of the newsletter
    :param week: the week of the newsletter
    :return: 302 RedirectResponse
    """
    newsletter_date = datetime.strptime(
        '%s-%s-1' % (year, week), '%Y-%W-%w')
    if date(int(year), 1, 4).isoweekday() > 4:
        newsletter_date -= timedelta(days=7)

    newsletter = get_object_or_404(Newsletter, date=newsletter_date)

    return redirect(newsletter.get_absolute_url(), permanent=True)


@staff_member_required
@permission_required('newsletters.send_newsletter')
def admin_send(request, pk):
    """
    If this is a GET request this view will render a confirmation
    page for the administrator. If it is a POST request the newsletter
    will be sent to all recipients

    :param request: the request object
    :param pk: the newsletter's primary key
    :return: 302 RedirectResponse if POST else 200 with the
             confirmation page HTML
    """
    newsletter = get_object_or_404(Newsletter, pk=pk)

    if newsletter.sent:
        return redirect(newsletter)

    if request.POST:
        emails.send_newsletter(request, newsletter)
        newsletter.sent = True
        newsletter.save()

        return redirect('admin:newsletters_newsletter_changelist')
    else:
        return render(request, 'newsletters/admin/send_confirm.html', {
            'newsletter': newsletter
        })
