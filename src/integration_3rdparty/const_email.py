import requests
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

from exchange_pubsub.google_pubsub import PubSub


class Client(object):
    def __init__(self, url: str):
        self.url = url

    def send(self, from_email, from_email_name, to_email, task, language, data):
        headers = {
            'Accept': 'application/json',
        }
        body = {
            'From': {
                'Address': from_email,
                'Name': from_email_name,
            },
            'To': {
                'Address': to_email,
                'Name': '',
            },
            # "Bccs": [
            #     "nqhieu841@gmail.com",
            #     "hieu.q1@autonomous.nyc"
            # ],
            # "Ccs": [
            #     "nqhieu842@gmail.com",
            #     "hieu.q2@autonomous.nyc"
            # ],
            'Type': task,
            'Lang': language,
            'Data': data,
        }
        resp = requests.post(self.url + '/request'.format(self.url),
                             json=body,
                             headers=headers, verify=False)

        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code in (401, 403, 500):
            raise AuthenticationFailed

        raise Exception('API issue HTTP Status {} Response {}'.format(resp.status_code, resp.content))


client = Client(settings.CONST_EMAIL_API['URL'])


class ConstantEmailManagement(object):
    @staticmethod
    def send(to_email: str, task: str, language: str, data: dict, from_email=None):
        from_email = from_email if from_email else settings.EMAIL_FROM_ADDRESS
        from_email_name = '' if None else settings.EMAIL_FROM_NAME

        return client.send(from_email, from_email_name, to_email, task, language, data)

    @staticmethod
    def send_by_pub(to_email: str, task: str, language: str, data: dict, from_email=None):
        from_email = from_email if from_email else settings.EMAIL_FROM_ADDRESS
        from_email_name = '' if None else settings.EMAIL_FROM_NAME

        body = {
            'From': {
                'Address': from_email,
                'Name': from_email_name,
            },
            'To': {
                'Address': to_email,
                'Name': '',
            },
            # "Bccs": [
            #     "nqhieu841@gmail.com",
            #     "hieu.q1@autonomous.nyc"
            # ],
            # "Ccs": [
            #     "nqhieu842@gmail.com",
            #     "hieu.q2@autonomous.nyc"
            # ],
            'Type': task,
            'Lang': language,
            'Data': data,
        }

        PubSub.send_email_message(body)
