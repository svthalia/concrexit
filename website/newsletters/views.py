from datetime import datetime, timedelta, date

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template
from django.utils import translation
from django.utils.translation import activate, get_language_info

from members.models import Member
from newsletters.models import Newsletter
from partners.models import Partner


def preview(request, pk, lang=None):
    newsletter = get_object_or_404(Newsletter, pk=pk)
    partners = Partner.objects.filter(is_main_partner=True)
    main_partner = partners[0] if len(partners) > 0 else None
    lang_code = request.LANGUAGE_CODE

    if lang is not None:
        try:
            get_language_info(lang)
            activate(lang)
            lang_code = lang
        except KeyError:
            # Language code not recognised by get_language_info
            pass

    return render(request, 'newsletters/email.html', {
        'newsletter': newsletter,
        'agenda_events': newsletter.newslettercontent_set.filter(
            newsletteritem=None).order_by('newsletterevent__start_datetime'),
        'main_partner': main_partner,
        'lang_code': lang_code
    })


def legacy_redirect(request, year, week):
    newsletter_date = datetime.strptime(
        '%s-%s-1' % (year, week), '%Y-%W-%w')
    if date(int(year), 1, 4).isoweekday() > 4:
        newsletter_date -= timedelta(days=7)

    newsletter = get_object_or_404(Newsletter, date=newsletter_date)

    return redirect(newsletter.get_absolute_url(), permanent=True)


@staff_member_required
@permission_required('newsletters.send_newsletter')
def admin_send(request, pk):
    newsletter = get_object_or_404(Newsletter, pk=pk)

    if newsletter.sent:
        return redirect(newsletter)

    if request.POST:
        partners = Partner.objects.filter(is_main_partner=True)
        main_partner = partners[0] if len(partners) > 0 else None

        from_email = settings.NEWSLETTER_FROM_ADDRESS
        html_template = get_template('newsletters/email.html')
        text_template = get_template('newsletters/email.txt')

        for language in settings.LANGUAGES:
            translation.activate(language[0])

            recipients = [member.email for member in
                          Member.active_members.all().filter(
                              profile__receive_newsletter=True,
                              profile__language=language[0])
                          if member.email]

            subject = '[THALIA] ' + newsletter.title

            context = {
                'newsletter': newsletter,
                'agenda_events': (
                    newsletter.newslettercontent_set
                    .filter(newsletteritem=None)
                    .order_by('newsletterevent__start_datetime')
                ),
                'main_partner': main_partner,
                'lang_code': language[0],
                'request': request
            }

            html_message = html_template.render(context)
            text_message = text_template.render(context)

            msg = EmailMultiAlternatives(subject, text_message,
                                         to=[from_email],
                                         bcc=recipients,
                                         from_email=from_email)
            msg.attach_alternative(html_message, "text/html")
            msg.send()

            translation.deactivate()

        newsletter.sent = True
        newsletter.save()

        return redirect('admin:newsletters_newsletter_changelist')
    else:
        return render(request, 'newsletters/admin/send_confirm.html', {
            'newsletter': newsletter
        })
