"""The emails defined by the newsletters package"""
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.utils import translation

from members.models import Member
from partners.models import Partner

from newsletters import services


def send_newsletter(request, newsletter):
    """
    Sends the newsletter as HTML and plaintext email

    :param request: the request object
    :param newsletter: the newsletter to be send
    """
    partners = Partner.objects.filter(is_main_partner=True)
    main_partner = partners[0] if len(partners) > 0 else None

    from_email = settings.NEWSLETTER_FROM_ADDRESS
    html_template = get_template('newsletters/email.html')
    text_template = get_template('newsletters/email.txt')

    for language in settings.LANGUAGES:
        translation.activate(language[0])

        recipients = [member.email for member in
                      Member.current_members.all().filter(
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

        services.write_to_file(newsletter.pk, language[0], html_message)

        translation.deactivate()
