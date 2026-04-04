from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "test-secret-key")
DEBUG = os.environ.get("DEBUG", "False") == "True"

ALLOWED_HOSTS = ["bearestate.me", "www.bearestate.me", "premain.bearestate.me", "127.0.0.1", "localhost", ]

CSRF_TRUSTED_ORIGINS = [
    "https://bearestate.me",
    "https://www.bearestate.me",
    "https://premain.bearestate.me",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# API KEYS
RENTCAST_API_KEY = os.environ.get("RENTCAST_API_KEY")


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'home',
    'behave_django',
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

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR.parent / 'templates'],
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

WSGI_APPLICATION = 'myproject.wsgi.application'


# Database

# Path name for the database that imports the databse path from a set enviornment variable named "DATABASE_PATH", and falls back to the default database if the
# file cannot be found
DATABASE_PATH = os.environ.get("DATABASE_PATH", str(BASE_DIR / "db.sqlite3"))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        # Set the database pathway to be what path DATABASE_PATH collected from the decleration above
        'NAME': DATABASE_PATH,
    }
}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Internationalization

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files

STATIC_URL = '/static/'
STATIC_ROOT = Path(os.environ.get("STATIC_ROOT_PATH", str(BASE_DIR / "staticfiles")))

# Media Files
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT_PATH", str(BASE_DIR / "media")))

# Login redirects

LOGIN_URL = '/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'


# Default primary key field type


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


