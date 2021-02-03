import logging
from decimal import Decimal

import requests
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

from constant_core.models import UserTx
from integration_3rdparty.exceptions import ConstantCoreNotEnoughBalanceException


class Client(object):
    def __init__(self, url: str):
        self.url = url

    def get_profile(self, token):
        headers = {
            'Authorization': 'Bearer {}'.format(token),
            'Accept': 'application/json'
        }
        resp = requests.get('{}/auth/profile'.format(self.url), headers=headers, verify=False)
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
        elif resp.status_code in (401, 403):
            raise AuthenticationFailed

        raise Exception('API issue HTTP Status {} Response {}'.format(resp.status_code, resp.content))

    def verify_admin_otp(self, token, code):
        headers = {
            'Accept': 'application/json',
        }
        resp = requests.get('{}/admin/check-otp?key={}&otp={}'.format(self.url, token, code),
                            headers=headers, verify=False)

        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code in (401, 403):
            raise AuthenticationFailed

        raise Exception('API issue HTTP Status {} Response {}'.format(resp.status_code, resp.content))

    def update_balance(self, data):
        headers = {
            'Accept': 'application/json',
        }
        body = {
            'Data': data,
        }
        resp = requests.post(self.url + '/user/constant-balance-custom'.format(self.url),
                             json=body,
                             headers=headers, verify=False)

        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code in (401, 403):
            raise AuthenticationFailed
        elif resp.status_code == 500:
            body = resp.json()
            logging.error('Data: {} Body: {}'.format(data, body))
            if body.get('Error', {}).get('Code') == -9004:
                raise ConstantCoreNotEnoughBalanceException

        raise Exception('API issue HTTP Status {} Response {}'.format(resp.status_code, resp.content))

    def reserve_purchase(self, user_id, data):
        headers = {
            'Accept': 'application/json',
        }
        resp = requests.post('{}/reserve/purchase/{}'.format(self.url, user_id),
                             json=data,
                             headers=headers, timeout=10)

        if resp.status_code == 200:
            if resp.content:
                return resp.json()
            else:
                return None
        elif resp.status_code in (401, 403):
            raise AuthenticationFailed

        raise Exception('API issue HTTP Status {} Response {}'.format(resp.status_code, resp.content))


client = Client(settings.CONST_CORE_API['URL'])


class BalanceBase:
    def __init__(self, user_id: int, reserve_type: int, amount: Decimal, reference=None, skip_check_debt=False):
        self.from_user_id = user_id
        self.reserve_type = reserve_type
        self.amount = amount
        self.reference = reference
        self.type = -1
        self.skip_check_debt = skip_check_debt

    def to_dict(self):
        return {
            'Type': self.type,
            'FromUserId': self.from_user_id,
            'Amount': int('{:.0f}'.format(self.amount * Decimal(100))),
            'PurposeType': self.reserve_type,
            'Reference': str(self.reference),
            'SkipCheckDebt': self.skip_check_debt
        }


class BalanceHold(BalanceBase):
    def __init__(self, user_id: int, reserve_type: int, amount: Decimal, reference=None, skip_check_debt=False):
        super(BalanceHold, self).__init__(user_id, reserve_type, amount, reference, skip_check_debt=skip_check_debt)
        self.type = UserTx.HoldConstantBalance


class BalanceRelease(BalanceBase):
    def __init__(self, user_id: int, reserve_type: int, amount: Decimal, reference=None):
        super(BalanceRelease, self).__init__(user_id, reserve_type, amount, reference)
        self.type = UserTx.ReleaseConstantBalance


class TransferBase(BalanceBase):
    def __init__(self, from_user_id: int, to_user_id: int, reserve_type: int, amount: Decimal,
                 reference=None, children: list = None, reserve=True):
        super(TransferBase, self).__init__(from_user_id, reserve_type, amount, reference)
        self.to_user_id = to_user_id
        self.children = children
        self.reserve = reserve

    def to_dict(self):
        return {
            'Type': self.type,
            'FromUserId': self.from_user_id,
            'ToUserId': self.to_user_id,
            'Amount': int('{:.0f}'.format(self.amount * Decimal(100))),
            'PurposeType': self.reserve_type,
            'Reference': str(self.reference),
            'Reserve': self.reserve,
            'Children': [child.to_dict() for child in self.children] if self.children else []
        }


class TransferBalance(TransferBase):
    def __init__(self, from_user_id: int, to_user_id: int, reserve_type: int, amount: Decimal,
                 reference=None, children: list = None, reserve=True):
        super(TransferBalance, self).__init__(from_user_id, to_user_id, reserve_type, amount,
                                              reference, children, reserve)
        self.type = UserTx.TransferConstantBalance


class TransferBalanceFromHold(TransferBase):
    def __init__(self, from_user_id: int, to_user_id: int, reserve_type: int, amount: Decimal,
                 reference=None, children: list = None, reserve=True):
        super(TransferBalanceFromHold, self).__init__(from_user_id, to_user_id, reserve_type, amount,
                                                      reference, children, reserve)
        self.type = UserTx.TransferConstantBalanceWithFromHolding


class TransferBalanceToHold(TransferBase):
    def __init__(self, from_user_id: int, to_user_id: int, reserve_type: int, amount: Decimal,
                 reference=None, children: list = None, reserve=True):
        super(TransferBalanceToHold, self).__init__(from_user_id, to_user_id, reserve_type, amount,
                                                    reference, children, reserve)
        self.type = UserTx.TransferConstantBalanceWithToHolding


class ConstantCoreManagement(object):
    @staticmethod
    def get_profile(token):
        return client.get_profile(token)

    @staticmethod
    def verify_otp(token, code):
        return client.verify_otp(token, code)

    @staticmethod
    def update_balance(balance_data: list):
        return client.update_balance([data.to_dict() for data in balance_data])

    @staticmethod
    def verify_admin_otp(token, code):
        return client.verify_admin_otp(token, code)

    @staticmethod
    def reserve_purchase(user_id, data: dict):
        input_data = {
            "Amount": int('{:.0f}'.format(data['amount'] * Decimal(100))),
            "Reference": "exchange_{}".format(data['id'])
        }
        return client.reserve_purchase(user_id, input_data)

    @staticmethod
    def reserve_plaid_purchase(user_id, data: dict):
        input_data = {
            "ReserveID": int(data['reserve_id']),
            "PlaidID": int(data['plaid_id'])
        }
        return client.reserve_purchase(user_id, input_data)
