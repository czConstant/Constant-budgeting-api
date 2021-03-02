import json
from unittest.mock import MagicMock

from budgeting.business.transaction import TransactionBusiness
from constant_core.business import ConstantCoreBusiness
from constant_core.models import User, Reserves, PlaidAccounts, AdminLogActions, AdminPermissions
from constant_core.queries import BackendQuery
from budgeting.business.notification import BudgetingNotification
from budgeting_pubsub.google_pubsub import PubSub

from integration_3rdparty.const_core import ConstantCoreManagement


class CoreMock(object):
    def get_user(self, user_id=1, data=None):
        user = User(
            id=user_id,
            user_name='exchange',
            full_name='Exchange Order',
            first_name='Exchange',
            last_name='Order',
            middle_name='',
            email='exchange@order.com',
            constant_balance=10000,
            constant_balance_holding=0,
            address_country='US',
            tax_country='US',
            status=1,
            verified_level=6,
            referral_code='REFERRAL',
            language='en',
            membership=1,
            withdraw_confirmed_email_on=0,
            suspend_withdrawal_to=None
        )
        if data:
            user.constant_balance = data.get('constant_balance', user.constant_balance)
            user.verified_level = data.get('verified_level', user.verified_level)
            user.agent_user = data.get('agent_user', user.agent_user)
            user.user_role_id = data.get('user_role_id', user.user_role_id)
            user.tax_country = data.get('tax_country', user.tax_country)
            user.lo_user = data.get('lo_user', user.lo_user)

        mock = MagicMock(return_value=user)
        ConstantCoreBusiness.get_user = mock

        return mock

    def get_user_by_email(self):
        mock = MagicMock(return_value=User(id=1))
        ConstantCoreBusiness.get_user_by_email = mock

        return mock

    def has_plaid_account(self, user_id=1, result=True):
        mock = MagicMock(return_value=result)
        ConstantCoreBusiness.has_plaid_account = mock

        return mock

    def hold_balance(self):
        mock = MagicMock(return_value={})
        ConstantCoreBusiness.hold_balance = mock

        return mock

    def release_balance(self):
        mock = MagicMock(return_value=True)
        ConstantCoreBusiness.release_balance = mock

        return mock

    def get_reserve_by_reference(self):
        mock = MagicMock(return_value=Reserves(id=1))
        ConstantCoreBusiness.get_reserve_by_reference = mock

        return mock

    def get_reserve_by_ref_id(self):
        mock = MagicMock(return_value=Reserves(id=1))
        ConstantCoreBusiness.get_reserve_by_ref_id = mock

        return mock

    def get_default_plaid_account(self):
        mock = MagicMock(return_value=PlaidAccounts(id=1))
        ConstantCoreBusiness.get_default_plaid_account = mock

        return mock

    def get_plaid_account(self, data=None):
        obj = PlaidAccounts(id=1,
                            institution_name='Plaid',
                            account_subtype='savings')
        if data:
            obj.id = data.get('id', obj.id)
        mock = MagicMock(return_value=obj)
        ConstantCoreBusiness.get_plaid_account = mock

        return mock

    def create_admin_log_action(self):
        mock = MagicMock(return_value=AdminLogActions(id=1))
        ConstantCoreBusiness.create_admin_log_action = mock

        return mock

    def update_obj(self):
        mock = MagicMock(return_value=None)
        ConstantCoreBusiness.update_obj = mock

        return mock


class CoreServiceMock(object):
    def verify_otp(self):
        mock = MagicMock(return_value={'Result': True})
        ConstantCoreManagement.verify_otp = mock

        return mock


class BackendQueryMock(object):
    def check_admin_permission(self):
        mock = MagicMock(return_value=[AdminPermissions(
            can_view=True,
            can_add=True,
            can_update=True,
            can_delete=True,
        ), ])
        BackendQuery.check_admin_permission = mock

        return mock


class TransactionBusinessMock(object):
    def import_transaction_from_plaid(self):
        mock = MagicMock(return_value=None)
        TransactionBusiness.import_transaction_from_plaid = mock
        return mock


class BudgetingNotificationMock(object):
    def noti_transaction_imported(self):
        mock = MagicMock(return_value=True)
        BudgetingNotification.noti_transaction_imported = mock

        return mock

    def noti_budget_end(self):
        mock = MagicMock(return_value=True)
        BudgetingNotification.noti_budget_end = mock

        return mock

    def noti_budget_over(self):
        mock = MagicMock(return_value=True)
        BudgetingNotification.noti_budget_over = mock

        return mock


class PubSubMock(object):
    def send_message(self):
        mock = MagicMock(return_value=True)
        PubSub.send_message = mock

        return mock
