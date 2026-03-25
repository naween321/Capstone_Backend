from .base import *
import os
from dotenv import load_dotenv

load_dotenv()
print(os.getenv('DJANGO_ENV'))
DEBUG = os.getenv('DJANGO_ENV') == "dev"

SECRET_KEY = os.getenv("SECRET_KEY")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    },

}

GROQ_API_KEY = os.getenv('GROQ_API_KEY')

PROTOTYPE_APP_KEY = os.getenv('PROTOTYPE_APP_KEY', '')
EXPENSE_SCAN_MONTHLY_QUOTA = int(os.getenv('EXPENSE_SCAN_MONTHLY_QUOTA', 100))
VERYFI_API_BASE_URL = os.getenv('VERYFI_API_BASE_URL', '')
VERYFI_API_CLIENT_ID = os.getenv('VERYFI_API_CLIENT_ID', '')
VERYFI_API_USERNAME = os.getenv('VERYFI_API_USERNAME', '')
VERYFI_API_KEY = os.getenv('VERYFI_API_KEY', '')

########### Settings for Development ###############
if DEBUG:
    ALLOWED_HOSTS = ['*']
    INSTALLED_APPS += ['drf_spectacular', ]
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    CELERY_RESULT_BACKEND = CELERY_BROKER_URL

######### Settings for Production #################
else:
    ALLOWED_HOSTS = []
    INSTALLED_APPS += []
