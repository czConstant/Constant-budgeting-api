import requests
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed


class Client(object):
    def __init__(self, url: str):
        self.url = url

    def webhook_constant(self, data):
        headers = {
            'Accept': 'application/json',
        }
        resp = requests.post('{}/webhook/constant'.format(self.url),
                             json=data,
                             headers=headers)

        if resp.status_code == 200:
            if resp.content:
                return resp.json()
            else:
                return None
        elif resp.status_code in (401, 403):
            raise AuthenticationFailed

        raise Exception('API issue HTTP Status {} Response {}'.format(resp.status_code, resp.content))

    def send_event(self, user_id, data):
        headers = {
            'Accept': 'application/json',
        }
        resp = requests.post('{}/webhook/internal/user/{}/event'.format(self.url, user_id),
                             json=data,
                             headers=headers)

        if resp.status_code == 200:
            if resp.content:
                return resp.json()
            else:
                return None
        elif resp.status_code in (401, 403):
            raise AuthenticationFailed

        raise Exception('API issue HTTP Status {} Response {}'.format(resp.status_code, resp.content))


client = Client(settings.CONST_HOOK_API['URL'])


class ConstantHookManagement(object):
    @staticmethod
    def send_notification(data: dict):
        input_data = {
            "type": 12,
            "data": {
                "Action": 0,
                "Data": data
            }
        }
        return client.webhook_constant(input_data)

    @staticmethod
    def send_event(user_id, event_type: dict, data: dict = {}):
        input_data = {
            "Event": event_type,
            "Data": data
        }
        return client.send_event(user_id, input_data)
