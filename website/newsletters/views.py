"""Views provided by the newsletters package."""

from django.contrib.admin import helpers
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.http.request import HttpRequest as HttpRequest
from django.http.response import HttpResponse as HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from newsletters import services
from newsletters.forms import NewsletterImportEventForm
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


class ImportEventView(FormView):
    form_class = NewsletterImportEventForm
    template_name = "newsletters/admin/import_events.html"
    admin = None
    newsletter = None

    @property
    def success_url(self):
        return reverse(
            "admin:newsletters_newsletter_change", args=(self.newsletter.pk,)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        media = self.admin.media + context["form"].media
        context.update(
            {
                **self.admin.admin_site.each_context(self.request),
                "app_label": "newsletters",
                "opts": self.newsletter._meta,
                "newsletter": self.newsletter,
                "title": _("Import events"),
                "media": media,
                "subtitle": f"{self.newsletter.title} ({self.newsletter.date})",
                "adminform": helpers.AdminForm(
                    context["form"],
                    ((None, {"fields": context["form"].fields.keys()}),),
                    {},
                ),
            }
        )
        return context

    def form_valid(self, form):
        form.import_events(self.newsletter)
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        self.newsletter = get_object_or_404(Newsletter, pk=self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)
