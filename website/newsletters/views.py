"""Views provided by the newsletters package."""
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, redirect, render

from newsletters import services
from newsletters.models import Newsletter
from partners.models import Partner
from utils.media.services import get_media_url


def preview(request, pk, lang=None):
    """View that renders the newsletter as HTML.

    :param request: the request object
    :param pk: the newsletter's primary key
    :return: HttpResponse 200 containing the newsletter HTML
    """
    newsletter = get_object_or_404(Newsletter, pk=pk)

    if newsletter.rendered_file:
        return redirect(get_media_url(newsletter.rendered_file))

    events = services.get_agenda(newsletter.date) if newsletter.date else None
    local_partners = services.split_local_partners()

    return render(
        request,
        "newsletters/email.html",
        {
            "newsletter": newsletter,
            "agenda_events": events,
            "main_partner": Partner.objects.filter(is_main_partner=True).first(),
            "local_partners": local_partners,
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
