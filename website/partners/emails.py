"""The emails defined by the partners package."""

from utils.snippets import send_email


def send_new_vacancy_email(vacancy, member):
    """Send an email

    """
    # TODO: Better mail, title, etc
    send_email(
        member.email,
        "New vacancy",
        "partners/email/new_vacancy_email.txt",
        {
            "partner": vacancy.partner.name,
            "title": vacancy.title,
            "url": vacancy.link,
            "description": vacancy.description,
        },
    )
