"""Add gratitude release fields + GratitudePrompt cache + clean stale cron rows."""

from django.db import migrations, models


def cleanup_stale_periodic_tasks(apps, schema_editor):
    """Drop any leftover PeriodicTask rows from the removed mood/todo plumbing."""
    try:
        PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')
    except LookupError:
        return
    PeriodicTask.objects.filter(
        task__in=[
            'commons.firebase.send_mood_reminder',
            'commons.firebase.send_scheduled_notification',
        ]
    ).delete()


def noop_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ('commons', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='devicetoken',
            name='gratitude_mode',
            field=models.CharField(
                choices=[
                    ('on_release', 'On prompt release'),
                    ('scheduled', 'Scheduled'),
                ],
                default='on_release',
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name='devicetoken',
            name='timezone',
            field=models.CharField(default='UTC', max_length=64),
        ),
        migrations.CreateModel(
            name='GratitudePrompt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('date', models.DateField(unique=True)),
                ('prompt', models.TextField()),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.RunPython(cleanup_stale_periodic_tasks, noop_reverse),
    ]
