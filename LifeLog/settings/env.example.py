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

########### Settings for Development ###############
if DEBUG:
    ALLOWED_HOSTS = ['*']
    INSTALLED_APPS += ['drf_spectacular', ]

######### Settings for Production #################
else:
    ALLOWED_HOSTS = []
    INSTALLED_APPS += []
