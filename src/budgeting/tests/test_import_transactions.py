from datetime import timedelta

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from budgeting.factories import WalletFactory
from common.business import get_now
from common.test_mocks import TransactionBusinessMock
from common.test_utils import AuthenticationUtils


class ImportPlaidTransactionJobTests(APITestCase):
    def setUp(self):
        self.auth_utils = AuthenticationUtils(self.client)
        self.user_id = self.auth_utils.system_login()

        self.url = reverse('budget-job:import-plaid-transaction-view')
        self.transaction_business_mock = TransactionBusinessMock()
        self.transaction_business_mock.import_transaction_from_plaid()

    def test_run_1(self):
        last_import = get_now().today() - timedelta(days=1)
        WalletFactory.create_batch(5, user_id=1, last_import=last_import, plaid_id=1)
        response = self.client.post(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['success'], 5)
        self.assertEqual(data['failed'], 0)
