"""The emails defined by the education package."""
import logging

from django.conf import settings
from django.core import mail
from django.template import loader
from django.urls import reverse

logger = logging.getLogger(__name__)


def send_document_notification(document):
    """Send an email to a configured email.

    :param document: The document we are sending the email for
    """
    admin_url = reverse(
        f"admin:{document._meta.app_label}_{document._meta.model_name}_change",
        args=(document.pk,),
    )

    email_body = loader.render_to_string(
        "education/email/document_notification.txt",
        {
            "document": document.name,
            "uploader": document.uploader.get_full_name(),
            "url": settings.BASE_URL + admin_url,
            "course": f"{document.course.name} ({document.course.course_code})",
        },
    )
    mail.EmailMessage(
        "Education document ready for review",
        email_body,
        settings.DEFAULT_FROM_EMAIL,
        [settings.EDUCATION_NOTIFICATION_ADDRESS],
    ).send()
