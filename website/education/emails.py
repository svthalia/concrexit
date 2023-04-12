"""The emails defined by the education package."""
import logging

from django.conf import settings
from django.urls import reverse

from utils.snippets import send_email

logger = logging.getLogger(__name__)


def send_document_notification(document):
    """Send an email to a configured email.

    :param document: The document we are sending the email for
    """
    admin_url = reverse(
        f"admin:{document._meta.app_label}_{document._meta.model_name}_change",
        args=(document.pk,),
    )

    send_email(
        to=[settings.EDUCATION_NOTIFICATION_ADDRESS],
        subject="Education document ready for review",
        txt_template="education/email/document_notification.txt",
        html_template="education/email/document_notification.html",
        context={
            "document": document.name,
            "uploader": document.uploader.get_full_name(),
            "url": settings.BASE_URL + admin_url,
            "course": f"{document.course.name} ({document.course.course_code})",
        },
    )
