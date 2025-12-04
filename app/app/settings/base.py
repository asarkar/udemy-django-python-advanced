"""
Base settings shared by all environments.
Do NOT put secrets here. Use environment variables for secret/config values.
"""

import atexit
import os
import shutil
import tempfile
from pathlib import Path

import environ  # type: ignore[import-untyped]

BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize env handler with sensible defaults
env = environ.Env(
    DEBUG=(bool, False),
)

# If a .env file exists at project root, read it (useful for local dev)
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    environ.Env.read_env(ENV_FILE)

# Basic / required settings (safely read from env where appropriate)
SECRET_KEY = env("SECRET_KEY", default="django-insecure-unsafe-local-secret")
DEBUG = env("DEBUG")

# ALLOWED_HOSTS default empty list (override in env for prod)
ALLOWED_HOSTS: list[str] = env.list("ALLOWED_HOSTS", default=[])

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
    "core",
    "user",
    "recipe",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "app.wsgi.application"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
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
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static & media
STATIC_URL = "/static/"
STATIC_ROOT = env("STATIC_ROOT", default=str(BASE_DIR / "staticfiles"))

MEDIA_URL = "/media/"

# MEDIA_ROOT: use env var if provided, otherwise create a temp directory per process
MEDIA_ROOT = env("MEDIA_ROOT", default=None)

if not MEDIA_ROOT:
    TMP_ROOT_NAME = "django_media"
    TMP_ROOT = os.path.join(tempfile.gettempdir(), TMP_ROOT_NAME)
    os.makedirs(TMP_ROOT, exist_ok=True)

    # per-run media dir under the consistent tmp root
    MEDIA_ROOT = os.path.join(TMP_ROOT, f"run_{os.getpid()}")
    os.makedirs(MEDIA_ROOT, exist_ok=True)

    # register cleanup only for the runserver worker process (not the autoreloader parent)
    if os.environ.get("RUN_MAIN") == "true":
        print(f"TMP_ROOT: {TMP_ROOT}")
        atexit.register(lambda: shutil.rmtree(TMP_ROOT, ignore_errors=True))

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Auth
AUTH_USER_MODEL = "core.User"

# DRF / Spectacular
REST_FRAMEWORK = {"DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema"}
SPECTACULAR_SETTINGS = {"COMPONENT_SPLIT_REQUEST": True}
