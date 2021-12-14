"""The emails defined by the promotion request package."""
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.utils.translation import gettext_lazy as _

from members.models import MemberGroup

def notify_new_request(request):

    text_template = get_template("requests/new_request_email.txt")

    subject = _("[THALIA][PAPARAZCIE] New promtion request for '{}'").format(
        request.event.title
    )
    text_message = text_template.render(
        {
            "event": request,
        }
    )

    paparazcie_object = MemberGroup.objects.filter(name = "Paparazcie")
    paparazcie_email = paparazcie_object.values().first()["contact_email"]

    EmailMessage(subject, text_message, to=[paparazcie_email]).send()