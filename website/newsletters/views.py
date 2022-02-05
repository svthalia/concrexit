"""Views provided by the newsletters package."""
import os

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import activate, get_language_info
from django_sendfile import sendfile

from newsletters import services
from newsletters.models import Newsletter
from partners.models import Partner


def preview(request, pk, lang=None):
    """View that renders the newsletter as HTML.

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
        settings.MEDIA_ROOT, "newsletters", f"{pk}_{lang_code}.html"
    )
    if os.path.isfile(file_path):
        return sendfile(request, file_path)

    newsletter = get_object_or_404(Newsletter, pk=pk)
    events = services.get_agenda(newsletter.date) if newsletter.date else None

    return render(
        request,
        "newsletters/email.html",
        {
            "newsletter": newsletter,
            "agenda_events": events,
            "main_partner": Partner.objects.filter(is_main_partner=True).first(),
            "local_partners": Partner.objects.filter(is_local_partner=True),
            "lang_code": lang_code,
        },
    )


@staff_member_required
@permission_required("newsletters.send_newsletter")
def admin_send(request, pk):
    """If this is a GET request this view will render a confirmation page for the administrator.

    If it is a POST request the newsletter will be sent to all recipients.

    :param request: the request object
    :param pk: the newsletter's primary key
    :return: 302 RedirectResponse if POST else 200 with the
             confirmation page HTML
    """
    newsletter = get_object_or_404(Newsletter, pk=pk)

    if newsletter.sent:
        return redirect(newsletter)

    if request.POST:
        services.send_newsletter(newsletter)

        return redirect("admin:newsletters_newsletter_changelist")

    return render(
        request, "newsletters/admin/send_confirm.html", {"newsletter": newsletter}
    )
