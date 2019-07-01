"""The emails defined by the newsletters package"""

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.utils import translation, timezone
from django.utils.timezone import make_aware

from members.models import Member
from newsletters import services
from partners.models import Partner


def send_newsletter(newsletter):
    """
    Sends the newsletter as HTML and plaintext email

    :param newsletter: the newsletter to be send
    """
    events = None
    if newsletter.date:
        datetime = make_aware(timezone.datetime(
            year=newsletter.date.year,
            month=newsletter.date.month,
            day=newsletter.date.day,
        )) if newsletter.date else None
        events = services.get_agenda(datetime)

    from_email = settings.NEWSLETTER_FROM_ADDRESS
    html_template = get_template('newsletters/email.html')
    text_template = get_template('newsletters/email.txt')

    main_partner = Partner.objects.filter(is_main_partner=True).first()
    local_partner = Partner.objects.filter(is_local_partner=True).first()

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
            'agenda_events': events,
            'main_partner': main_partner,
            'local_partner': local_partner,
            'lang_code': language[0]
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
