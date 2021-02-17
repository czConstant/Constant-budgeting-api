"""
Django settings for coin_exchange project.

Generated by 'django-admin startproject' using Django 2.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""
import datetime
import logging
import sys
from decimal import Decimal
from os.path import abspath, basename, dirname, join, normpath

from corsheaders.defaults import default_headers
from sentry_sdk.integrations.logging import LoggingIntegration

DJANGO_ROOT = dirname(dirname(abspath(__file__)))
SITE_ROOT = dirname(DJANGO_ROOT)
SITE_NAME = basename(DJANGO_ROOT)
sys.path.append(DJANGO_ROOT)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = dirname(DJANGO_ROOT)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '^v#98ng3c5lhop**jd1cgw_qhn@z%skj(zb7+d!$7w4p%r9!&5'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
TEST = True
UNIT_TEST = False

ALLOWED_HOSTS = []

SYSTEM_TOKEN = 'xxx'

# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'django_extensions',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'django_filters',
]

LOCAL_APPS = [
    'budgeting',
    'budgeting_pubsub',
    'constant_core',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'common.http.RequestLogMiddleware'
]

ROOT_URLCONF = 'conf.urls'

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

WSGI_APPLICATION = 'conf.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3' if 'test' in sys.argv else 'django.db.backends.mysql',
        'NAME': ':memory:' if 'test' in sys.argv else 'constant_local_exchange',
        'USER': 'root',
        'PASSWORD': '123456',
        'HOST': '127.0.0.1',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': 'SET character_set_connection=utf8mb4;'
                            'SET collation_connection=utf8mb4_unicode_ci;'
                            "SET NAMES 'utf8mb4';"
                            "SET CHARACTER SET utf8mb4;"
        },
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

MEDIA_ROOT = normpath(join(SITE_ROOT, 'media'))
MEDIA_URL = '/media/'
STATIC_ROOT = normpath(join(SITE_ROOT, 'assets'))
STATIC_URL = '/static/'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'common.http.custom_exception_handler',
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'budgeting_auth.authentication.BudgetingAuthentication',
    ),
}

JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(seconds=60 * 60)
}

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_HEADERS = list(default_headers) + [
    'ip',
    'otp',
    'recaptcha',
    'otpphone',
    'otptoken',
    'country',
    'platform',
    'os',
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{message}',
            'style': '{',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/elk/filebeat/exchange-api.log',
            'maxBytes': 15728640,  # 1024 * 1024 * 15B = 15MB
            'backupCount': 10,
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': True,
        },
        'kibana': {
            'handlers': ['file'],
            'propagate': False,
        }
    }
}

PUBLIC_TOKEN = "UCVZZXB45WPETnmaZQeh2FhW8JmLbmVFFeHe4NQr3KcRLqT9"

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-budgeting',
    }
}

TINYMCE_DEFAULT_CONFIG = {
    'width': '80%',
    'height': '300px'
}

# All of this is already happening by default!
sentry_logging = LoggingIntegration(
    level=logging.INFO,  # Capture info and above as breadcrumbs
    event_level=logging.ERROR  # Send errors as events
)

EMAIL_FROM_NAME = 'Justin from Constant'
EMAIL_FROM_ADDRESS = "justin@myconstant.com"

# GOOGLE_CLOUD_PROJECT = 'coin-exchange'
# STORAGE_BUCKET = 'coin-exchange-staging'

# FRONTEND_HOST = 'http://staging.coinbowl.com'
# API_HOST = 'http://localhost:8000/api'

RECAPTCHA_SECRET = '6LdjFLQUAAAAAB-Ykbw5tn5YMUwU_i1ndieIS2W2'

PUBSUB = {
    'TOPIC_ID': 'event-topic',
    'EMAIL_TOPIC_ID': 'email-topic',
    'EXCHANGE_SUB_ID': 'event-topic-sub-exchange',
    'SAVING_SUB_ID': 'event-topic-sub-saving',
    'BACKEND_SUB_ID': 'event-topic-sub-backend',
    'BUDGETING_SUB_ID': 'event-topic-sub-budgeting',
}

CONST_API = {
    'URL': 'http://backend-service:6666/api',
    'SECRET_KEY': 'abc@123',
}

CONST_EXCHANGE_API = {
    'URL': 'http://exchange-backend-service:6670/exchange-api',
    'TOKEN': 'xxx',
}

CONST_SAVING_API = {
    'URL': 'http://saving-backend-service:6671/saving-api/saving-job',
    'TOKEN': 'xxx',
}

CONST_BUDGETING_API = {
    'URL': 'http://budgeting-backend-service:6673/budgeting-api',
    'TOKEN': 'xxx'
}

CONST_HOOK_API = {
    'URL': 'http://webhook-constant-service:8100/api'
}

CONST_EMAIL_API = {
    'URL': 'http://constant-email:8888'
}

CONST_CORE_API = {
    'URL': 'http://constant-core-service:9090'
}

PLAID_API = {
    "URL": "https://sandbox.plaid.com",
    "CLIENT_ID": "5efd315f4ba6640012dc8019",
    "SECRET": "456cab4f77591fe5e12fa39532ff79"
}

FRONT_END_URL = 'https://staging.constant.money'

SYSTEM_ACCOUNT = 0

DEFAULT_AGENT_EMAIL = 'operation@constant.money'
