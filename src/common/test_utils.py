from unittest.mock import MagicMock

from django.conf import settings
from rest_framework.test import APIClient

from budgeting_auth.authentication import ReCaptchaPermission
from integration_3rdparty.const import ConstantManagement


class AuthenticationUtils(object):
    def __init__(self, client: APIClient, username: str = 'test_username@email.com'):
        self.client = client
        self.username = username

    def user_login(self, username: str = None, user_id: int = None):
        username = username if username else self.username
        user_id = 1 if not user_id else user_id
        ConstantManagement.auth_check = MagicMock(return_value={
            'Result': {
                'ID': user_id,
                'UserName': username,
                'FullName': username,
                'Email': username,
            }
        })
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + username)
        return user_id

    def system_login(self, username: str = None):
        username = username if username else self.username
        user_id = 999
        ConstantManagement.auth_check = MagicMock(return_value={
            'Result': {
                'ID': 1,
                'UserName': username,
                'FullName': username,
                'Email': username,
                'RoleID': 999,
            }
        })
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + settings.SYSTEM_TOKEN)
        return user_id

    def user_recaptcha(self):
        ReCaptchaPermission.captcha_auth = MagicMock(return_value=True)

    def admin_login(self, username: str = None):
        username = username if username else self.username
        ConstantManagement.auth_check = MagicMock(return_value={
            'Result': {
                'ID': 1,
                'UserName': username,
                'FullName': username,
                'Email': username,
                'RoleID': 1,
            }
        })
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + username)

    def agent_login(self, username: str = None):
        username = username if username else self.username
        ConstantManagement.auth_check = MagicMock(return_value={
            'Result': {
                'ID': 1,
                'UserName': username,
                'FullName': username,
                'Email': username,
                'RoleID': 1,
            }
        })
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + username)

    def verify_otp(self):
        mock = MagicMock(return_value={
            'Result': True
        })
        ConstantManagement.verify_otp_2 = mock
        return mock
