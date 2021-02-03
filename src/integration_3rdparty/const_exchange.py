from decimal import Decimal

import requests
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed


class Client(object):
    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token

    def send_pubsub_task(self, task, message_id, data=None):
        headers = {
            'Authorization': 'Bearer {}'.format(self.token),
            'Accept': 'application/json'
        }
        resp = requests.post('{}/exchange-sub/task/{}/{}/'.format(self.url, task, message_id),
                             data=data, headers=headers, verify=False, timeout=0.5)
        if resp.status_code in (200, 201):
            return resp.json()
        elif resp.status_code in (401, 403):
            raise AuthenticationFailed

        raise Exception('API issue HTTP Status {} Response {}'.format(resp.status_code, resp.content))


client = Client(settings.CONST_EXCHANGE_API['URL'],
                settings.CONST_EXCHANGE_API['TOKEN'])


class ConstantExchangeManagement(object):
    @staticmethod
    def send_pubsub_task(task, message_id, data):
        return client.send_pubsub_task(task, message_id, data)
