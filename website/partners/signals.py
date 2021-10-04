"""The signals checked by the partners package."""
from django.db.models.signals import m2m_changed

from partners import emails
from utils.models.signals import suspendingreceiver

from members.models.member import Member
from partners.models import Vacancy


@suspendingreceiver(
    m2m_changed,
    sender=Vacancy.categories.through,
    dispatch_uid="partners_vacancy_categories_m2m_changed",
)
def post_vacancy_save(sender, instance, action, **kwargs):
    """Send emails to subscribers of the vacancy categories."""
    if action == "post_add" and not instance.mail_sent:
        subscribers = Member.objects.filter(
            vacancycategory__in=instance.categories.all()
        ).distinct()
        for subscriber in subscribers:
            emails.send_new_vacancy_email(instance, subscriber)

        instance.mail_sent = True
        instance.save()
