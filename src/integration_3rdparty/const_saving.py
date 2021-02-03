from decimal import Decimal

import requests
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed


class Client(object):
    pass


client = Client(settings.CONST_SAVING_API['URL'],
                settings.CONST_SAVING_API['TOKEN'])


class ConstantSavingManagement(object):
    pass