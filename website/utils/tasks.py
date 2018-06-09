from django.utils import timezone
from thaliawebsite import celery_app
from django.conf import settings


def schedule_task(task, args=(), eta=timezone.now()):
    if settings.CELERY_ENABLED:
        result = task.apply_async(args, eta=eta)
        return result.id
    return None


def revoke_task(task_id):
    if settings.CELERY_ENABLED:
        celery_app.control.revoke(task_id)
