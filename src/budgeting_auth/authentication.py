import logging

import requests
from django.conf import settings
from rest_framework import authentication, permissions
from rest_framework.authentication import get_authorization_header

from constant_core.queries import BackendQuery
from budgeting.models import ConstUser, SystemConstUser
from integration_3rdparty.const import ConstantManagement


class BudgetingAuthentication(authentication.BaseAuthentication):
    keyword = 'bearer'

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None, None

        token = auth[1].decode()
        system_token = settings.SYSTEM_TOKEN

        if system_token == token:
            user = SystemConstUser(
                user_id=1,
                username=system_token,
                first_name='admin',
                email='admin',
            )
        else:
            user_data = ConstantManagement.auth_check(auth[1].decode())['Result']
            user = ConstUser(
                user_id=user_data['ID'],
                username=user_data['UserName'],
                first_name=user_data['FullName'],
                email=user_data['Email'],
                token=token
            )
        return user, None

    def authenticate_header(self, request):
        return 'Bearer'


class AdminPermission(permissions.BasePermission):
    """
    Admin permission.
    """

    def has_permission(self, request, view):
        return request.user and request.user.role_id > 0


class SystemPermission(permissions.BasePermission):
    """
    Admin permission.
    """

    def has_permission(self, request, view):
        return request.user and request.user.role_id == 999 and request.user.username == settings.SYSTEM_TOKEN


class OTPPermission(permissions.BasePermission):
    keyword = 'bearer'

    def has_permission(self, request, view):
        auth = get_authorization_header(request).split()
        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None
        token = auth[1].decode()
        otp_code = request.META.get('HTTP_OTP', None)
        otp_token = request.META.get('HTTP_OTPTOKEN', None)
        otp_phone = request.META.get('HTTP_OTPPHONE', None)
        data = ConstantManagement.verify_otp_2(token, otp_code, otp_token, otp_phone)
        if data['Result']:
            return True
        self.message = data['Code']
        return False


class ReCaptchaPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        captcha_code_1 = request.META.get('HTTP_RECAPTCHA', '')
        captcha_code_2 = request.META.get('HTTP_X_RECAPTCHA', '')

        captcha_code = captcha_code_1 if captcha_code_1 else captcha_code_2
        if captcha_code:
            url = 'https://www.google.com/recaptcha/api/siteverify?secret={}&response={}'.format(
                settings.RECAPTCHA_SECRET,
                captcha_code
            )
            resp = requests.post(url)

            if resp.status_code == 200:
                data = resp.json()
                if data.get('success'):
                    return True

            logging.error(resp.json())

        return False


class CreateReCaptchaPermission(ReCaptchaPermission):
    def has_permission(self, request, view):
        return view.action != 'create' or super(CreateReCaptchaPermission, self).has_permission(request, view)


class CreateOTPPermission(OTPPermission):
    def has_permission(self, request, view):
        return view.action != 'create' or super(CreateOTPPermission, self).has_permission(request, view)


class PutOTPPermission(OTPPermission):
    def has_permission(self, request, view):
        return request.method != 'PUT' or super(PutOTPPermission, self).has_permission(request, view)


class AdminRolePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        qs = BackendQuery.check_admin_permission(request.user.user_id, self.get_page_name())
        obj = None
        if qs:
            obj = qs[0]
        if obj:
            if self.check_action() == 'can_view':
                return obj.can_view
            if self.check_action() == 'can_add':
                return obj.can_add
            if self.check_action() == 'can_update':
                return obj.can_update
            if self.check_action() == 'can_delete':
                return obj.can_delete
        return False

    def get_page_name(self):
        return ''

    def check_action(self):
        return ''


class AdminRoleViewPermission(AdminRolePermission):
    def check_action(self):
        return 'can_view'


class AdminRoleAddPermission(AdminRolePermission):
    def check_action(self):
        return 'can_add'


class AdminRoleUpdatePermission(AdminRolePermission):
    def check_action(self):
        return 'can_update'


class AdminRoleDeletePermission(AdminRolePermission):
    def check_action(self):
        return 'can_delete'
