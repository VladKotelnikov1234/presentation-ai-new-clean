from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Безопасный секретный ключ (замените на случайный или используйте переменную окружения)
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-1234567890abcdef')  # Для безопасности лучше взять из переменной окружения
DEBUG = False  # Отключаем для продакшена
ALLOWED_HOSTS = ['service-lessons.onrender.com']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'video_processor.apps.VideoProcessorConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Первое место для CORS
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CORS настройки для фронтенда на Render
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend.onrender.com",  # Замените на URL вашего фронтенда после деплоя
]
CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "OPTIONS",
]
CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "http-referer",
    "x-title",
]
CORS_ALLOW_CREDENTIALS = True  # Для работы с cookies, если нужно

# CSRF настройки
CSRF_TRUSTED_ORIGINS = [
    "https://your-frontend.onrender.com",  # Замените на URL вашего фронтенда
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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
STATIC_ROOT = '/opt/render/project/src/static'  # Путь для сбора статических файлов на Render

MEDIA_URL = '/media/'
MEDIA_ROOT = '/media'  # Соответствует Persistent Disk на Render

REST_FRAMEWORK = {
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
