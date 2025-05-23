from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-1234567890abcdef')
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    'service-lessons.onrender.com',
    'localhost',
    '127.0.0.1',
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'video_processor.apps.VideoProcessorConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'static'],  # Добавляем папку static для поиска index.html
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

REST_FRAMEWORK = {
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
}

# API-ключи (только из окружения, без значений по умолчанию)
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
SYNTHESIA_API_KEY = os.getenv('SYNTHESIA_API_KEY')
IOINTELLIGENCE_API_KEY = os.getenv('IOINTELLIGENCE_API_KEY')

#if not ELEVENLABS_API_KEY or not SYNTHESIA_API_KEY or not IOINTELLIGENCE_API_KEY:
    #import logging
    #logger = logging.getLogger(__name__)
    #logger.error("Одна или несколько API-ключи не заданы")
    #raise ValueError("Отсутствуют необходимые API-ключи")

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'