from pathlib import Path
import os
from urllib.parse import urlparse


BASE_DIR = Path(__file__).resolve().parent.parent
# Project root (folder that contains manage.py and top-level 'static/')
PROJECT_ROOT = BASE_DIR.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-secret-key")
# DEBUG is true when DJANGO_DEBUG == "1"
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"
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
    "fretes.middleware.LoginRequiredForAppMiddleware",
    "fretes.middleware.AuditMiddleware",
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

# Database configuration
# Priority: DATABASE_URL -> POSTGRES_* env -> SQLite fallback
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    # Ex.: postgres://user:pass@db:5432/fretes
    import dj_database_url
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
elif os.getenv("POSTGRES_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "fretes"),
            "USER": os.getenv("POSTGRES_USER", "fretes"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
            "HOST": os.getenv("POSTGRES_HOST", "db"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": 600,
        }
    }
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# Static
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Include top-level /app/static directory
_top_static = PROJECT_ROOT / "static"
STATICFILES_DIRS = [_top_static] if _top_static.exists() else []
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
# Respect Host header from proxy (preserves :port in links)
USE_X_FORWARDED_HOST = True
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "1") == "1"
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "1") == "1"
