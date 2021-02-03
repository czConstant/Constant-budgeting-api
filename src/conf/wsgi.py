"""
WSGI config for coin_exchange project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os

import requests
from django.core.wsgi import get_wsgi_application


def get_database_settings(db_key: str, prefix_key):
    resp = requests.get('http://constant-evn/secret?secret={}'.format(db_key))
    database_str = resp.json()['Result']

    database_parts = database_str.split(';;;')
    items = [
        ('host=', '{}_DB_HOST'.format(prefix_key)),
        ('port=', '{}_DB_PORT'.format(prefix_key)),
        ('database=', '{}_DB_NAME'.format(prefix_key)),
        ('username=', '{}_DB_USER'.format(prefix_key)),
        ('password=', '{}_DB_PASSWORD'.format(prefix_key)),
    ]
    for i in range(len(items)):
        if database_parts[i].startswith(items[i][0]):
            os.environ.setdefault(items[i][1], database_parts[i].replace(items[i][0], ''))


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings.local')
get_database_settings('DB-EXCHANGE-URL', 'EXCHANGE')
get_database_settings('DB-BACKEND-URL', 'BACKEND')
get_database_settings('DB-READ-EXCHANGE-URL', 'EXCHANGE_READ')
get_database_settings('DB-READ-BACKEND-URL', 'BACKEND_READ')

application = get_wsgi_application()
