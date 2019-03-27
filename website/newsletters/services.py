import os

from django.conf import settings
from django.template.loader import get_template
from django.utils import translation

from partners.models import Partner


def write_to_file(pk, lang, html_message):
    """
    Write newsletter to a file
    """
    cache_dir = os.path.join(settings.MEDIA_ROOT, 'newsletters')
    if not os.path.isdir(cache_dir):
        os.makedirs(cache_dir)

    with open(os.path.join(
        cache_dir,
        f'{pk}_{lang}.html'
    ), 'w+') as cache_file:
        cache_file.write(html_message)


def save_to_disk(newsletter, request):
    """
    Writes the newsletter as HTML to file (in all languages)
    """
    partners = Partner.objects.filter(is_main_partner=True)
    main_partner = partners[0] if len(partners) > 0 else None

    html_template = get_template('newsletters/email.html')

    for language in settings.LANGUAGES:
        translation.activate(language[0])

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

        write_to_file(newsletter.pk, language[0], html_message)
