from datetime import datetime
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from budgeting.factories import WalletFactory, CategoryFactory, BudgetFactory, TransactionFactory
from budgeting.models import Transaction
from common.test_utils import AuthenticationUtils


class BudgetTests(APITestCase):
    def setUp(self):
        self.auth_utils = AuthenticationUtils(self.client)
        self.user_id = self.auth_utils.user_login()
        self.url = reverse('budget:budget-list')

    def test_add(self):
        wallet = WalletFactory()
        cat = CategoryFactory()

        data = {
            'category': cat.id,
            'wallet': wallet.id,
            'amount': '1000',
            'from_date': '2021-01-02',
            'to_date': '2021-02-02',
        }
        response = self.client.post(self.url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update(self):
        budget = BudgetFactory(user_id=self.user_id)
        wallet = WalletFactory()
        cat = CategoryFactory()

        data = {
            'category': cat.id,
            'wallet': wallet.id,
            'amount': '1000',
            'from_date': '2021-01-02',
            'to_date': '2021-02-02',
        }
        response = self.client.put(self.url + '{}/'.format(budget.id), data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete(self):
        budget = BudgetFactory(user_id=self.user_id)
        response = self.client.delete(self.url + '{}/'.format(budget.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_list(self):
        wallet = WalletFactory()
        cat = CategoryFactory()
        BudgetFactory(user_id=self.user_id, wallet=wallet, category=cat, amount=Decimal(1000),
                      from_date=datetime(2021, 1, 1), to_date=datetime(2100, 1, 31))
        TransactionFactory.create_batch(3, user_id=self.user_id, transaction_at=datetime(2021, 1, 1),
                                        wallet=wallet, category=cat)
        TransactionFactory.create_batch(3, user_id=self.user_id, transaction_at=datetime(2021, 1, 31),
                                        wallet=wallet, category=cat)
        response = self.client.get(self.url + '?wallet_id=' + str(wallet.id), format='json')
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(data[0]['current_amount']), Decimal(60))
        self.assertEqual(Decimal(data[0]['is_end']), False)
        self.assertEqual(Decimal(data[0]['is_over']), False)

    def test_list_is_over(self):
        wallet = WalletFactory()
        cat = CategoryFactory()
        BudgetFactory(user_id=self.user_id, wallet=wallet, category=cat, amount=Decimal(50),
                      from_date=datetime(2021, 1, 1), to_date=datetime(2100, 1, 31))
        TransactionFactory.create_batch(3, user_id=self.user_id, transaction_at=datetime(2021, 1, 1),
                                        wallet=wallet, category=cat)
        TransactionFactory.create_batch(3, user_id=self.user_id, transaction_at=datetime(2021, 1, 31),
                                        wallet=wallet, category=cat)
        response = self.client.get(self.url + '?wallet_id=' + str(wallet.id) + '&is_over=1', format='json')
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(data[0]['current_amount']), Decimal(60))
        self.assertEqual(Decimal(data[0]['is_end']), False)
        self.assertEqual(Decimal(data[0]['is_over']), True)

    def test_list_is_end(self):
        wallet = WalletFactory()
        cat = CategoryFactory()
        BudgetFactory(user_id=self.user_id, wallet=wallet, category=cat, amount=Decimal(100),
                      from_date=datetime(2021, 1, 1), to_date=datetime(2021, 1, 31))
        TransactionFactory.create_batch(3, user_id=self.user_id, transaction_at=datetime(2021, 1, 1),
                                        wallet=wallet, category=cat)
        TransactionFactory.create_batch(3, user_id=self.user_id, transaction_at=datetime(2021, 1, 31),
                                        wallet=wallet, category=cat)
        response = self.client.get(self.url + '?wallet_id=' + str(wallet.id) + '&is_end=1', format='json')
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(data[0]['current_amount']), Decimal(60))
        self.assertEqual(Decimal(data[0]['is_end']), True)
        self.assertEqual(Decimal(data[0]['is_over']), False)
