from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env. Real values must never live in this
# file; see .env.example for the required keys.
load_dotenv(BASE_DIR / ".env")


def env_flag(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is not set. Copy .env.example to .env and generate one with: "
        "python -c \"from django.core.management.utils import get_random_secret_key "
        "as g; print(g())\""
    )

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_flag("DEBUG", default=False)

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]



# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'results',
    'students',
    'authen',

    'storages',
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

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATES_DIRS := BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases
#
# Local development uses the bundled SQLite db.sqlite3 and needs no external
# services. The hosted Postgres is opt-in via USE_DATABASE_URL so a DATABASE_URL
# left over in a local .env can never silently redirect `runserver` or
# `migrate` at a production database.

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
USE_DATABASE_URL = env_flag("USE_DATABASE_URL", default=False)

if DATABASE_URL and not USE_DATABASE_URL:
    import sys

    print(
        "\nWARNING: DATABASE_URL is set but USE_DATABASE_URL is not; using the "
        "local SQLite database instead.\n"
        "         Set USE_DATABASE_URL=True to target the hosted database.\n",
        file=sys.stderr,
    )

if USE_DATABASE_URL:
    if not DATABASE_URL:
        raise RuntimeError(
            "USE_DATABASE_URL is set but DATABASE_URL is empty. "
            "Either provide DATABASE_URL or unset USE_DATABASE_URL to use SQLite."
        )
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
    # Managed Postgres (Supabase, Neon, ...) requires TLS.
    if not DATABASE_URL.startswith("sqlite"):
        DATABASES["default"]["OPTIONS"] = {"sslmode": "require"}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = '/static/'

# for development
STATICFILES_DIRS = [BASE_DIR / 'static']

# for production later
STATIC_ROOT = BASE_DIR / 'staticfiles'


# image files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Auth
LOGIN_URL = "/staff/login/"
LOGIN_REDIRECT_URL = "/result/manage/"
LOGOUT_REDIRECT_URL = "/staff/login/"


# Supabase Storage (S3-compatible).
# Credentials come from the environment only. Rotate any key that has ever
# been committed to the repository.
AWS_ACCESS_KEY_ID = os.getenv("SUPABASE_S3_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("SUPABASE_S3_SECRET_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("SUPABASE_BUCKET", "images")
AWS_S3_ENDPOINT_URL = os.getenv(
    "SUPABASE_S3_ENDPOINT_URL",
    "https://lfnlcezieopmrqgegnnm.supabase.co/storage/v1/s3",
)
AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "eu-west-1")
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = False
AWS_S3_ADDRESSING_STYLE = "path"
AWS_DEFAULT_ACL = "public-read"

# Media is served from Supabase only when credentials are actually configured,
# otherwise uploads fall back to the local MEDIA_ROOT above.
USE_SUPABASE_STORAGE = bool(AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY)

STORAGES = {
    "default": {
        "BACKEND": (
            "config.storage_backends.SupabaseStorage"
            if USE_SUPABASE_STORAGE
            else "django.core.files.storage.FileSystemStorage"
        )
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        if not DEBUG
        else "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}


# Security hardening. These only apply once DEBUG is off, so local development
# over plain http keeps working.
if not DEBUG:
    SECURE_SSL_REDIRECT = env_flag("SECURE_SSL_REDIRECT", default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    X_FRAME_OPTIONS = "DENY"
    # Behind a proxy (Render, Fly, nginx) so the correct scheme is detected.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


