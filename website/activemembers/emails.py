from django.conf import settings
from django.template import loader
from django.utils.translation import gettext_lazy as _


def send_gsuite_welcome_message(member, email, password):
    """Send an email to notify a member of G Suite credentials.

    :param member: the member
    :param email: G Suite primary email
    :param password: randomly generated password
    """
    email_body = loader.render_to_string(
        "activemembers/email/gsuite_info.txt",
        {
            "full_name": member.get_full_name(),
            "username": email,
            "password": password,
            "url": settings.BASE_URL,
        },
    )
    member.email_user(_("Your new G Suite credentials"), email_body)


def send_gsuite_suspended_message(member):
    """Send an email to notify a member of G Suite suspension.

    :param member: the member
    """
    email_body = loader.render_to_string(
        "activemembers/email/gsuite_suspend.txt",
        {"full_name": member.get_full_name(), "url": settings.BASE_URL},
    )
    member.email_user(_("G Suite account suspended"), email_body)
