import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# ─────────────────────────────────────────
# Base directory & load .env
# ─────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

# ─────────────────────────────────────────
# Core settings
# ─────────────────────────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY", "replace-me")

# Detect if we're on localhost (dev) or production
IS_LOCALHOST = "127.0.0.1" in os.environ.get("ALLOWED_HOSTS", "") or "localhost" in os.environ.get("ALLOWED_HOSTS", "")

# Debug auto-switch
DEBUG = IS_LOCALHOST or os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost").split(",")

# ─────────────────────────────────────────
# Installed Apps
# ─────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "results",
    "authen",
]

# ─────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # production static files
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ─────────────────────────────────────────
# Database (SQLite dev / Postgres prod)
# ─────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL")

if DEBUG and IS_LOCALHOST:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
elif DATABASE_URL:
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
else:
    raise Exception("No DATABASE_URL set for production!")

# ─────────────────────────────────────────
# Password validation
# ─────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]

# ─────────────────────────────────────────
# Internationalization
# ─────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ─────────────────────────────────────────
# Static & Media
# ─────────────────────────────────────────
STATIC_URL = os.environ.get("STATIC_URL", "/static/")
MEDIA_URL = os.environ.get("MEDIA_URL", "/media/")

STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_ROOT = BASE_DIR / "media"

# ─────────────────────────────────────────
# Auth / Redirects
# ─────────────────────────────────────────
LOGIN_URL = os.environ.get("LOGIN_URL", "/staff/login/")
LOGIN_REDIRECT_URL = os.environ.get("LOGIN_REDIRECT_URL", "/result/manage/")
LOGOUT_REDIRECT_URL = os.environ.get("LOGOUT_REDIRECT_URL", "/staff/login/")

# ─────────────────────────────────────────
# Security (Production)
# ─────────────────────────────────────────
SECURE_SSL_REDIRECT = not DEBUG and os.environ.get("SECURE_SSL_REDIRECT", "False").lower() in ("true", "1", "yes")
SESSION_COOKIE_SECURE = not DEBUG and os.environ.get("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1", "yes")
CSRF_COOKIE_SECURE = not DEBUG and os.environ.get("CSRF_COOKIE_SECURE", "False").lower() in ("true", "1", "yes")
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", 0))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get("SECURE_HSTS_INCLUDE_SUBDOMAINS", "False").lower() in ("true", "1", "yes")
SECURE_HSTS_PRELOAD = os.environ.get("SECURE_HSTS_PRELOAD", "False").lower() in ("true", "1", "yes")
