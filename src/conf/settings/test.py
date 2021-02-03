from .base import *  # noqa

DEBUG = True
UNIT_TEST = True

SYSTEM_TOKEN = 'xxx'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'constant',
        'USER': 'root',
        'PASSWORD': 'qazq@z123',
        'HOST': 'localhost',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': 'SET character_set_connection=utf8mb4;'
                            'SET collation_connection=utf8mb4_unicode_ci;'
                            "SET NAMES 'utf8mb4';"
                            "SET CHARACTER SET utf8mb4;"
        },
    },
    "constant": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# When using random users make sure they're created quickly
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.CryptPasswordHasher',
)

LOGGING = {}
