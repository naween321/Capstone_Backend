from .base import *

DEBUG = True

SECRET_KEY = "test-secret-key"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "test_db",
        "USER": "test_user",
        "PASSWORD": "test_password",
        "HOST": "localhost",
        "PORT": "5432",
    }
}

GROQ_API_KEY = "test-api-key"


ALLOWED_HOSTS = ['*']
INSTALLED_APPS += ['drf_spectacular', ]
CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
