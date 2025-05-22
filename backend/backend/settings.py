from pathlib import Path
import os

# Путь к базовой директории проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Секретный ключ (лучше хранить в переменной окружения)
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-1234567890abcdef')  # Замените в продакшене

# Режим отладки (False для продакшена)
DEBUG = os.getenv('DEBUG', 'False') == 'True'  # Позволяет включать отладку через переменную окружения

# Разрешённые хосты
ALLOWED_HOSTS = [
    'service-lessons.onrender.com',
    'localhost',
    '127.0.0.1',
]

# Установленные приложения
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

# Промежуточное ПО
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

# CORS настройки
CORS_ALLOWED_ORIGINS = [
    "https://lessons-brmd.onrender.com",  # URL твоего фронтенда
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
    "HTTP-Referer",  # Исправлено для OpenRouter
    "X-Title",
]
CORS_ALLOW_CREDENTIALS = True

# CSRF настройки
CSRF_TRUSTED_ORIGINS = [
    "https://lessons-brmd.onrender.com",  # URL фронтенда
]

# URL-конфигурация
ROOT_URLCONF = 'backend.urls'

# Настройки шаблонов
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

# WSGI приложение
WSGI_APPLICATION = 'backend.wsgi.application'

# Настройки базы данных
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Локализация
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Статические файлы
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Относительный путь для Render
STATICFILES_DIRS = [BASE_DIR / 'static']  # Дополнительные директории для статических файлов, если нужно

# Медиафайлы
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'  # Относительный путь для Persistent Disk на Render

# Настройки REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
}

# API-ключи (через переменные окружения)
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY', 'sk_1a928b668fcdd7667d58bbdfeae0e0b77347f6e863c9775f')
SYNTHESIA_API_KEY = os.getenv('SYNTHESIA_API_KEY', '399b87cac1835dd1e65602af9fe8a2b3')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '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')

# Автоинкрементные поля
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'