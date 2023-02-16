from django.conf import settings
from django.template import loader
from django.utils.translation import gettext_lazy as _

from utils.snippets import send_email


def send_gsuite_welcome_message(member, email, password):
    """Send an email to notify a member of G Suite credentials.

    :param member: the member
    :param email: G Suite primary email
    :param password: randomly generated password
    """
    send_email(
        to=[member.email],
        subject="Your new G Suite credentials",
        txt_template="activemembers/email/gsuite_info.txt",
        html_template="activemembers/email/gsuite_info.html",
        context={
            "full_name": member.get_full_name(),
            "username": email,
            "password": password,
            "url": settings.BASE_URL,
        },
    )


def send_gsuite_suspended_message(member):
    """Send an email to notify a member of G Suite suspension.

    :param member: the member
    """
    send_email(
        to=[member.email],
        subject="G Suite account suspended",
        txt_template="activemembers/email/gsuite_suspend.txt",
        html_template="activemembers/email/gsuite_suspend.html",
        context={
            "full_name": member.get_full_name(),
            "url": settings.BASE_URL,
        },
    )
