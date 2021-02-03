import hashlib
import logging

import requests
from django.conf import settings
from requests.adapters import HTTPAdapter
from rest_framework.exceptions import AuthenticationFailed
from urllib3 import Retry


class Client(object):
    def __init__(self, url: str, secret_key: str):
        self.url = url
        self.secret_key = secret_key

    def get_profile(self, token):
        headers = {
            'Authorization': 'Bearer {}'.format(token),
            'Accept': 'application/json'
        }
        resp = requests.get('{}/auth/profile'.format(self.url), headers=headers, verify=False)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code in (401, 403, 500):
            raise AuthenticationFailed

        raise Exception('API issue HTTP Status {} Response {}'.format(resp.status_code, resp.content))

    def auth_check(self, token):
        headers = {
            'Authorization': 'Bearer {}'.format(token),
            'Accept': 'application/json'
        }

        session = requests.Session()
        retry = Retry(connect=2, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        resp = session.get('{}/auth/check'.format(self.url), headers=headers, verify=False)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code in (401, 403):
            raise AuthenticationFailed

        raise Exception('API issue HTTP Status {} Response {}'.format(resp.status_code, resp.content))

    def verify_otp(self, token, code):
        headers = {
            'Authorization': 'Bearer {}'.format(token),
            'Accept': 'application/json',
        }
        resp = requests.post('{}/auth/verifyOTP'.format(self.url),
                             json={
                                 'OTP': code,
                             },
                             headers=headers, verify=False)

        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 500:
            return {
                'Result': False
            }
        elif resp.status_code in (401, 403):
            raise AuthenticationFailed

        raise Exception('API issue HTTP Status {} Response {}'.format(resp.status_code, resp.content))

    def verify_otp_2(self, token, otp_code, otp_token, otp_phone):
        headers = {
            'Authorization': 'Bearer {}'.format(token),
            'Accept': 'application/json',
            'OTP': otp_code,
            'OTPToken': otp_token,
            'OTPPhone': otp_phone,
        }
        resp = requests.post('{}/auth/verify-otp'.format(self.url),
                             headers=headers, verify=False)

        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 500:
            return {
                'Result': False,
                'Code': resp.json().get('Error', {}).get('Code')
            }
        elif resp.status_code in (401, 403):
            raise AuthenticationFailed

        raise Exception('API issue HTTP Status {} Response {}'.format(resp.status_code, resp.content))


client = Client(settings.CONST_API['URL'], settings.CONST_API['SECRET_KEY'])


class ConstantManagement(object):
    @staticmethod
    def get_profile(token):
        return client.get_profile(token)

    @staticmethod
    def verify_otp(token, code):
        return client.verify_otp(token, code)

    @staticmethod
    def verify_otp_2(token, otp_code, otp_token, otp_phone):
        return client.verify_otp_2(token, otp_code, otp_token, otp_phone)

    @staticmethod
    def auth_check(token):
        return client.auth_check(token)
