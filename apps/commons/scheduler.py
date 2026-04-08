from django_celery_beat.models import CrontabSchedule, PeriodicTask
import json

TASK_NAME_PREFIX = "mood_reminder_device_"


def _task_name(device_id: int) -> str:
    return f"{TASK_NAME_PREFIX}{device_id}"


def upsert_mood_reminder(device_id: int, hour: int, minute: int, days_of_week: str):
    """
    days_of_week: comma-separated cron day numbers, e.g. "1,3,5" for Mon/Wed/Fri.
    Sunday=0, Monday=1, ..., Saturday=6.
    """
    task_name = _task_name(device_id)

    # Delete existing schedule if present
    PeriodicTask.objects.filter(name=task_name).delete()

    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute=str(minute),
        hour=str(hour),
        day_of_week=days_of_week,
        day_of_month="*",
        month_of_year="*",
    )

    PeriodicTask.objects.create(
        name=task_name,
        task="commons.firebase.send_mood_reminder",
        crontab=schedule,
        args=json.dumps([device_id]),
        enabled=True,
    )


def delete_mood_reminder(device_id: int):
    PeriodicTask.objects.filter(name=_task_name(device_id)).delete()
