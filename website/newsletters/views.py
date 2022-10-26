"""Views provided by the newsletters package."""
import os

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.core.files.storage import DefaultStorage
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import activate, get_language_info

from newsletters import services
from newsletters.models import Newsletter
from partners.models import Partner
from utils.media.services import get_media_url


def preview(request, pk, lang=None):
    """View that renders the newsletter as HTML.

    :param request: the request object
    :param pk: the newsletter's primary key
    :param lang: the language of the render
    :return: HttpResponse 200 containing the newsletter HTML
    """
    lang_code = request.LANGUAGE_CODE
    storage = DefaultStorage()

    if lang is not None:
        try:
            get_language_info(lang)
            activate(lang)
            lang_code = lang
        except KeyError:
            # Language code not recognised by get_language_info
            pass

    # Send cached file, if it exists
    file_path = os.path.join("newsletters", f"{pk}_{lang_code}.html")
    if storage.exists(file_path):
        return redirect(get_media_url(file_path))

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
