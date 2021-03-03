from datetime import datetime
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from budgeting.factories import WalletFactory, CategoryFactory, BudgetFactory, TransactionFactory
from common.test_utils import AuthenticationUtils


class JobTests(APITestCase):
    def setUp(self):
        self.auth_utils = AuthenticationUtils(self.client)
        self.user_id = self.auth_utils.system_login()

    def test_list_is_end(self):
        url = reverse('budget-job:end-budget-notify-view')
        wallet = WalletFactory()
        cat = CategoryFactory()
        BudgetFactory(user_id=self.user_id, wallet=wallet, category=cat, amount=Decimal(100),
                      from_date=datetime(2021, 1, 1), to_date=datetime(2021, 1, 31))

        response = self.client.post(url, format='json')
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
