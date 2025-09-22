import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def env(name, default=None, cast=None):
    val = os.getenv(name, default)
    if val is None:
        return None
    if cast is list:
        return [x.strip() for x in val.split(",") if x.strip()]
    return val

SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-only-unsafe")
DEBUG = env("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = env("ALLOWED_HOSTS", "127.0.0.1,localhost", cast=list)
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS", "", cast=list)

TIME_ZONE = env("TIME_ZONE", "America/Sao_Paulo")
USE_TZ = True

INSTALLED_APPS = [
    "django.contrib.admin","django.contrib.auth","django.contrib.contenttypes",
    "django.contrib.sessions","django.contrib.messages","django.contrib.staticfiles",
    # apps
    "fretes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # servir static em prod
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "fretes_web.urls"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {
        "context_processors": [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
        ],
    },
}]

WSGI_APPLICATION = "fretes_web.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "fretes"),
        "USER": env("POSTGRES_USER", "fretes"),
        "PASSWORD": env("POSTGRES_PASSWORD", "fretes"),
        "HOST": env("POSTGRES_HOST", "db"),
        "PORT": env("POSTGRES_PORT", "5432"),
    }
}

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {"django.request": {"level": "ERROR", "handlers": ["console"], "propagate": False}},
}
