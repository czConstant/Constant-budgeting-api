from datetime import timedelta

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from budgeting.business.transaction import TransactionBusiness
from budgeting.constants import DIRECTION
from budgeting.factories import WalletFactory, CategoryFactory
from budgeting.models import Category
from common.business import get_now
from common.test_mocks import TransactionBusinessMock, BudgetingNotificationMock, CoreMock, PlaidManagementMock
from common.test_utils import AuthenticationUtils


class ImportPlaidTransactionJobTests(APITestCase):
    def setUp(self):
        self.auth_utils = AuthenticationUtils(self.client)
        self.user_id = self.auth_utils.system_login()

        self.url = reverse('budget-job:import-plaid-transaction-view')
        self.transaction_business_mock = TransactionBusinessMock()
        self.import_transaction_from_plaid_mock, self.import_transaction_from_plaid_original = \
            self.transaction_business_mock.import_transaction_from_plaid()
        self.notification_mock = BudgetingNotificationMock()

    def tearDown(self):
        TransactionBusiness.import_transaction_from_plaid = self.import_transaction_from_plaid_original

    def test_run_1(self):
        noti_transaction_imported_mock = self.notification_mock.noti_transaction_imported()
        last_import = get_now().today() - timedelta(days=1)
        WalletFactory.create_batch(5, user_id=1, last_import=last_import, plaid_id=1)
        response = self.client.post(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['success'], 5)
        self.assertEqual(data['failed'], 0)
        self.assertEqual(noti_transaction_imported_mock.call_count, 5)


class ImportPlaidTransactionTests(APITestCase):
    def setUp(self) -> None:
        self.core_mock = CoreMock()
        self.plaid_management_mock = PlaidManagementMock()

        CategoryFactory(code=Category.DEFAULT_CODE, direction=DIRECTION.income)
        CategoryFactory(code=Category.DEFAULT_CODE, direction=DIRECTION.expense)

    def test_run_1(self):
        get_plaid_account_mock = self.core_mock.get_plaid_account()
        get_transaction_mock = self.plaid_management_mock.get_transaction()

        user_id = 1
        to_date = get_now().today()
        last_import = to_date - timedelta(days=1)
        wallet = WalletFactory(user_id=user_id, last_import=last_import, plaid_id=1)
        TransactionBusiness.import_transaction_from_plaid(user_id, wallet=wallet,
                                                          from_date=last_import, to_date=to_date)

        self.assertEqual(get_plaid_account_mock.call_count, 1)
        self.assertEqual(get_transaction_mock.call_count, 1)
