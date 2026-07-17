import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')
load_dotenv(BASE_DIR.parent / '.env')
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key-change-in-prod')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0,testserver').split(',') if h.strip()]
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if origin.strip()]
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'core.apps.CoreConfig',
    'accounts.apps.AccountsConfig',
    'jobs.apps.JobsConfig',
    'employers.apps.EmployersConfig',
    'applications.apps.ApplicationsConfig',
    'ai_tools.apps.AiToolsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'jobfinder.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
            'core.context_processors.global_context',
        ],
    },
}]

WSGI_APPLICATION = 'jobfinder.wsgi.application'

import os as _os

# ── Base de données ──────────────────────────────────────────────────────────
# DB_ENGINE=mysql  →  MySQL 8.4 LTS (production / phpMyAdmin)
# DB_ENGINE=sqlite →  SQLite (développement / thèse)
_DB_ENGINE = _os.getenv('DB_ENGINE', 'mysql')

if _DB_ENGINE == 'mysql':
    DATABASES = {
        'default': {
            'ENGINE': 'jobfinder.db_backend',
            'NAME': _os.getenv('DB_NAME', 'jobfinder_db'),
            'USER': _os.getenv('DB_USER', 'root'),
            'PASSWORD': _os.getenv('DB_PASSWORD', ''),
            'HOST': _os.getenv('DB_HOST', 'localhost'),
            'PORT': _os.getenv('DB_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES', default_storage_engine=INNODB",
            },
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


AUTH_USER_MODEL = 'accounts.User'
AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]
LOGIN_URL          = '/auth/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE     = 'Africa/Abidjan'
USE_I18N = True
USE_TZ   = True

STATIC_URL      = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT     = BASE_DIR / 'staticfiles'

# Django 5.x : STATICFILES_STORAGE remplacé par STORAGES
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# IA Gratuite — Groq (https://console.groq.com — 100% gratuit)
GROQ_API_KEY   = os.getenv('GROQ_API_KEY', '')
GROQ_MODEL     = 'llama-3.1-8b-instant'
GROQ_MODEL_SMART = 'llama-3.3-70b-versatile'

JOBS_PER_PAGE  = 15

from django.contrib.messages import constants as msg
MESSAGE_TAGS = {
    msg.DEBUG:   'info',
    msg.INFO:    'info',
    msg.SUCCESS: 'success',
    msg.WARNING: 'warning',
    msg.ERROR:   'error',
}

EMAIL_BACKEND    = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'JobFinder AI <noreply@jobfinder.ai>'
