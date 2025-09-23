from pathlib import Path
import os
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-secret-key")
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "0"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": { "console": {"class": "logging.StreamHandler"} },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.server": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}
# Allow configuring hosts via environment variable (comma-separated)
# Example: ALLOWED_HOSTS=example.com,10.1.1.104,localhost
_allowed_hosts_env = os.getenv("ALLOWED_HOSTS", "").split(",")
ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts_env if h.strip()] or ["10.1.1.104"]

# Support both DJANGO_CSRF_TRUSTED_ORIGINS and CSRF_TRUSTED_ORIGINS
_csrf_origins_env = os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS") or os.getenv("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [h.strip() for h in _csrf_origins_env.split(",") if h.strip()]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_filters",
    "fretes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "fretes_web.urls"

TEMPLATES = [
    {
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
    },
]

WSGI_APPLICATION = "fretes_web.wsgi.application"

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    # Ex.: postgres://user:pass@db:5432/fretes
    import dj_database_url
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# Static
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
STORAGES = {
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}
}


# WhiteNoise: serve compressed static files
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
}

# Segurança extra em prod
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "1") == "1"
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "1") == "1"
