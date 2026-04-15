"""Register the daily Groq fetch + hourly cohort dispatcher in celery beat.

This project uses ``django_celery_beat.schedulers.DatabaseScheduler``, so beat
entries live in the database rather than CELERY_BEAT_SCHEDULE. We create them
via a data migration so a fresh install picks them up without requiring an
operator to add them through the admin.
"""

from django.db import migrations


DAILY_FETCH_TASK = 'commons.tasks.fetch_daily_gratitude_prompt'
HOURLY_DISPATCH_TASK = 'commons.tasks.dispatch_gratitude_release'


def install_beat_entries(apps, schema_editor):
    try:
        CrontabSchedule = apps.get_model('django_celery_beat', 'CrontabSchedule')
        PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')
    except LookupError:
        return

    # Daily prompt fetch — 09:00 UTC (≈ 4-5am ET / 1-2am PT, US is asleep).
    daily_cron, _ = CrontabSchedule.objects.get_or_create(
        minute='0',
        hour='9',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
        timezone='UTC',
    )
    PeriodicTask.objects.update_or_create(
        name='Fetch daily gratitude prompt (Groq)',
        defaults={
            'task': DAILY_FETCH_TASK,
            'crontab': daily_cron,
            'enabled': True,
            'description': 'Caches a single daily prompt from Groq for fan-out.',
        },
    )

    # Hourly cohort dispatcher — top of every UTC hour. The task itself
    # filters by tz cohorts whose local hour == 18 (6pm).
    hourly_cron, _ = CrontabSchedule.objects.get_or_create(
        minute='0',
        hour='*',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
        timezone='UTC',
    )
    PeriodicTask.objects.update_or_create(
        name='Dispatch gratitude release (per-TZ 6pm)',
        defaults={
            'task': HOURLY_DISPATCH_TASK,
            'crontab': hourly_cron,
            'enabled': True,
            'description': 'Pushes today\'s prompt to on_release devices whose local hour is 18.',
        },
    )


def remove_beat_entries(apps, schema_editor):
    try:
        PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')
    except LookupError:
        return
    PeriodicTask.objects.filter(
        task__in=[DAILY_FETCH_TASK, HOURLY_DISPATCH_TASK]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0002_gratitude_release'),
        ('django_celery_beat', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(install_beat_entries, remove_beat_entries),
    ]
