"""
Django settings for feed_aggregator project.

Generated by 'django-admin startproject' using Django 3.2.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import os
from pathlib import Path
from urllib.parse import urlparse

import pytz
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env files
load_dotenv("data/.env")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-ut^e0pt(8g)wzhok&0hjitv#)c^pcq=#0jj9nx0vx%w_xslr(3"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "true").lower() == "true"
DEBUG = True
print(f'Debug modus is turned {"on" if DEBUG else "off"}')

MAIN_HOST = os.environ.get("MAIN_HOST", "http://localhost")
HOSTS = os.environ.get("HOSTS", "http://localhost,http://127.0.0.1/").split(",")
CSRF_TRUSTED_ORIGINS = HOSTS
ALLOWED_HOSTS = [urlparse(url).netloc for url in HOSTS]
CORS_ALLOWED_ORIGINS = HOSTS


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "celery",
    "import_export",
    "rest_framework",
    "rest_framework.authtoken",
    "django_extensions",
    "djoser",
    "webpush",
    "pwa",
    "articles",
    "feeds",
    "preferences",
    "markets",
]


REST_FRAMEWORK = {
    "DEFAULT_METADATA_CLASS": "rest_framework.metadata.SimpleMetadata",
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("JWT",),
}


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

MIGRATION_MODULES = {
    "articles": "data.db_migrations.articles",
    "feeds": "data.db_migrations.feeds",
    "preferences": "data.db_migrations.preferences",
    "markets": "data.db_migrations.markets",
}

ROOT_URLCONF = "feed_aggregator.urls"

TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            TEMPLATES_DIR,
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "feed_aggregator.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "data/db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

PWA_APP_THEME_COLOR = "#dee2e6"
PWA_APP_BACKGROUND_COLOR = "#ffffff"
PWA_APP_DISPLAY = "standalone"
PWA_APP_SCOPE = "/"
PWA_APP_START_URL = "/"
PWA_APP_ORIENTATION = "any"
PWA_APP_ICONS = [{"src": "/static/apple-touch-icon.png", "sizes": "180x180"}]
PWA_APP_SPLASH_SCREEN = [
    {
        "rel": "apple-touch-startup-image",
        "media": (
            f"(device-width: {int(width)*int(scale)}px) and "
            f"(device-height: {int(height)*int(scale)}px) and "
            f"(-webkit-device-pixel-ratio: {scale}) and "
            f"(orientation: {'landscape' if int(width) > int(height) else 'portrait'})"
        ),
        "src": f"/static/splashscreens/{file}",
    }
    for file, width, height, scale in [
        (
            f,
            int(f.split("_")[0]),
            int(f.split("_")[1]),
            int(f.split("_")[2].split(".")[0]),
        )
        for f in os.listdir("./static/splashscreens")
        if os.path.isfile(os.path.join("./static/splashscreens", f))
        and ".png" in f
        and len(f.split("_")) == 4
    ]
]
PWA_APP_DIR = "ltr"


PWA_APP_LANG = LANGUAGE_CODE = "en-uk"
ALLOWED_LANGUAGES = os.getenv("ALLOWED_LANGUAGES", "*")
SIDEBAR_TITLE = os.getenv("SIDEBAR_TITLE", "Latest News")

TIME_ZONE = os.getenv("TIME_ZONE", "Europe/London")
TIME_ZONE_OBJ = pytz.timezone(TIME_ZONE)

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Celery settings
CELERY_BROKER_URL = "redis://localhost:6379"
CELERY_RESULT_BACKEND = "redis://localhost:6379"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://localhost:6379",
    }
}

# Webpush
WEBPUSH_SETTINGS = {
    "VAPID_PUBLIC_KEY": os.environ.get("WEBPUSH_PUBLIC_KEY"),
    "VAPID_PRIVATE_KEY": os.environ.get("WEBPUSH_PRIVATE_KEY"),
    "VAPID_ADMIN_EMAIL": "admin@example.com",
}

# Custom Variables
FULL_TEXT_URL = os.environ.get("FULL_TEXT_URL")
FEED_CREATOR_URL = os.environ.get("FEED_CREATOR_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PWA_APP_DESCRIPTION = PWA_APP_NAME = CUSTOM_PLATFORM_NAME = os.getenv(
    "CUSTOM_PLATFORM_NAME", "Personal News Platform"
)
