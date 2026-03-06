import os
from celery import Celery

# Set default Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "LifeLog.settings")

app = Celery("LifeLog")

# Load settings from Django settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto discover tasks inside installed apps
app.autodiscover_tasks()
