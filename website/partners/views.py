from random import random

import datetime

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.core.mail import EmailMessage

from partners.models import Partner, Vacancy, VacancyCategory


def index(request):
    partners = Partner.objects.filter(is_active=True, is_main_partner=False)
    try:
        main_partner = Partner.objects.get(
            is_active=True,
            is_main_partner=True
        )
    except Partner.DoesNotExist:
        main_partner = None

    context = {
        'main_partner': main_partner,
        'partners': sorted(partners, key=lambda x: random()),
    }
    return render(request, 'partners/index.html', context)


def partner(request, slug):
    partner = get_object_or_404(Partner, slug=slug)
    context = {
        'partner': partner,
        'vacancies': Vacancy.objects.filter(partner=partner),
    }
    return render(request, 'partners/partner.html', context)


def vacancies(request):
    context = {
        'vacancies': Vacancy.objects.exclude(
            expiration_date__lte=timezone.now().date()).order_by('?'),
        'categories': VacancyCategory.objects.all(),
    }

    return render(request, 'partners/vacancies.html', context)


def send_vacancy_expiration_mails():
    # Select vacencies that expire in roughly a month, wherefor
    # a mail hasn't been sent yet to Mr/Mrs Extern
    expired_vacancies = Vacancy.objects.filter(
        expiration_mail_sent=False,
        expiration_date__lt=timezone.now().date() + datetime.timedelta(days=30)
    )
    for exp_vacancy in expired_vacancies:
        # Create Message
        subject = "[THALIA][SPONSOR] Vacature '{}' van {} loopt af" \
            .format(exp_vacancy.title, exp_vacancy.get_company_name())
        text_message = "Hallo Extern,\n\nde vacature van {}, " \
                       "'{}' loopt over ca. een maand af. " \
                       "Misschien wil je ze contacteren om een " \
                       "nieuwe deal te sluiten.\n\n" \
                       "Groetjes,\nDe Website" \
            .format(exp_vacancy.title, exp_vacancy.get_company_name())
        recipient = "sponsor@thalia.nu"

        # Send Mail
        EmailMessage(
            subject,
            text_message,
            to=recipient
        ).send()

        # Save that mail has been sent into database
        exp_vacancy.expiration_mail_sent = True
        exp_vacancy.save()

    return HttpResponse(status=200)
