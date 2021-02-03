import json
import logging
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import Q

from common.business import get_now, generate_random_code_2
from constant_core.exceptions import NotEnoughBalanceException
from constant_core.models import User, Reserves, UserBank, AdminLogActions, PlaidAccounts, UserExtraInfo
from constant_core.serializers import BankSerializer, SimpleUserSerializer
from integration_3rdparty.const_core import ConstantCoreManagement, TransferBalance, BalanceHold, BalanceRelease, \
    TransferBalanceFromHold, TransferBalanceToHold


class ConstantCoreBusiness(object):
    @staticmethod
    def transfer(from_user_id: int, to_user_id: int, amount: Decimal):
        from_user = User.objects.get(id=from_user_id)
        if from_user.constant_balance_friendly < amount:
            raise NotEnoughBalanceException(balance=amount)

        ConstantCoreManagement.update_balance([
            TransferBalance(from_user_id, to_user_id, Reserves.RESERVE_TYPE_TRANSFER, amount)
        ])

    @staticmethod
    def hold_balance(user_id: int, amount: Decimal, reserve_type: int, order_id: int = None):
        user = User.objects.get(id=user_id)
        if user.constant_balance_friendly < amount:
            raise NotEnoughBalanceException(balance=amount)

        ConstantCoreManagement.update_balance([
            BalanceHold(user_id, reserve_type, amount, order_id)
        ])

    @staticmethod
    def release_balance(user_id: int, amount: Decimal, reserve_type: int, order_id: int = None):
        user = User.objects.get(id=user_id)
        if user.constant_balance_holding_friendly < amount:
            raise NotEnoughBalanceException(balance=amount)

        ConstantCoreManagement.update_balance([
            BalanceRelease(user_id, reserve_type, amount, order_id)
        ])

    @staticmethod
    def get_reserve(rid: int):
        return Reserves.objects.filter(id=rid).first()

    @staticmethod
    def get_last_reserve(user_id: int, reserve_type: int):
        return Reserves.objects.filter(to_user_id=user_id, reserve_type=reserve_type).last()

    @staticmethod
    def get_reserve_by_ext_id(ext_id: int, reserve_type: int):
        return Reserves.objects.filter(ext_id=ext_id, reserve_type=reserve_type).first()

    @staticmethod
    def get_reserve_by_ref_id(ref_id: int, reserve_type: int):
        return Reserves.objects.filter(ref_id=ref_id, reserve_type=reserve_type).first()

    @staticmethod
    def get_reserve_by_reference(reference: str):
        return Reserves.objects.filter(reference=reference).first()

    @staticmethod
    def get_user(user_id: int):
        return User.objects.get(id=user_id)

    @staticmethod
    def get_users(user_ids: list):
        return User.objects.filter(id__in=user_ids)

    @staticmethod
    def get_user_by_email(email: str):
        return User.objects.filter(email=email).first()

    @staticmethod
    def create_admin_log_action(request):
        obj = AdminLogActions.objects.create(
            user_id=request.user.user_id,
            request_url=request.path,
            request_body=json.dumps(request.data) if request.data else '',
            user_agent=request.META.get('HTTP_USER_AGENT'),
            proto='HTTP/1.1',
            client_ip=request.META.get('REMOTE_ADDR'),
            referer=request.META.get('HTTP_REFERER'),
            method=request.method,
        )

        return obj

    @staticmethod
    def update_obj(obj):
        obj.save()

    @staticmethod
    def update_last_withdraw(user_id):
        obj = UserExtraInfo.objects.filter(user_id=user_id).first()
        if obj:
            obj.last_withdraw = get_now()
            obj.save()


def admin_log(func, request, *args, **kwargs):
    try:
        if request.method != 'GET':
            obj = ConstantCoreBusiness.create_admin_log_action(request)
            response = func(*args, **kwargs)
            response_content = json.dumps(response.data, cls=DjangoJSONEncoder) if response.data else ''

            obj.response = response_content
            ConstantCoreBusiness.update_obj(obj)

            return response
        else:
            return func(*args, **kwargs)
    except Exception as e:
        logging.exception(e)
        raise
