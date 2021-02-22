from datetime import datetime
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from budgeting.constants import DIRECTION
from budgeting.factories import CategoryFactory, TransactionFactory, WalletFactory, CategoryGroupFactory
from common.test_utils import AuthenticationUtils


class CategoryGroupTests(APITestCase):
    def setUp(self):
        group_1 = CategoryGroupFactory(name='Group 1')
        group_2 = CategoryGroupFactory(name='Group 2')
        CategoryFactory.create_batch(5, group=group_1, direction=DIRECTION.income)
        CategoryFactory.create_batch(5, group=group_2, direction=DIRECTION.expense)
        self.url = reverse('budget:categorygroup-list')

    def test_list(self):
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_list_filter(self):
        response = self.client.get(self.url + '?direction=' + DIRECTION.income, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)


class CategoryTests(APITestCase):
    def setUp(self):
        CategoryFactory.create_batch(10)
        self.url = reverse('budget:category-list')

    def test_list(self):
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 10)


class WalletTests(APITestCase):
    def setUp(self):
        self.auth_utils = AuthenticationUtils(self.client)
        self.user_id = self.auth_utils.user_login()
        WalletFactory.create_batch(10, user_id=self.user_id)
        self.url = reverse('budget:wallet-list')

    def test_list(self):
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Wallet number 0
        self.assertEqual(len(response.json()), 10 + 1)

    def test_balance(self):
        wallet = WalletFactory(user_id=self.user_id)
        # +50
        TransactionFactory.create_batch(5, user_id=1, transaction_at=datetime(2021, 1, 1),
                                        direction=DIRECTION.income, wallet=wallet)
        # -20
        TransactionFactory.create_batch(2, user_id=1, transaction_at=datetime(2021, 1, 1),
                                        direction=DIRECTION.expense, wallet=wallet)
        # +30
        TransactionFactory.create_batch(3, user_id=1, transaction_at=datetime(2021, 2, 1),
                                        direction=DIRECTION.income, wallet=wallet)
        # -10
        TransactionFactory.create_batch(1, user_id=1, transaction_at=datetime(2021, 2, 1),
                                        direction=DIRECTION.expense, wallet=wallet)

        # +20
        TransactionFactory.create_batch(2, user_id=1, transaction_at=datetime(2021, 1, 1),
                                        direction=DIRECTION.income)
        # -10
        TransactionFactory.create_batch(1, user_id=1, transaction_at=datetime(2021, 1, 1),
                                        direction=DIRECTION.expense)
        # +40
        TransactionFactory.create_batch(4, user_id=1, transaction_at=datetime(2021, 2, 1),
                                        direction=DIRECTION.income)
        # -20
        TransactionFactory.create_batch(2, user_id=1, transaction_at=datetime(2021, 2, 1),
                                        direction=DIRECTION.expense)

        url = reverse('budget:wallet-balance')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(Decimal(data[1]['income_amount']), Decimal(80))
        self.assertEqual(Decimal(data[1]['expense_amount']), Decimal(30))
        self.assertEqual(Decimal(data[1]['balance']), Decimal(50))

        self.assertEqual(Decimal(data[0]['income_amount']), Decimal(60))
        self.assertEqual(Decimal(data[0]['expense_amount']), Decimal(30))
        self.assertEqual(Decimal(data[0]['balance']), Decimal(30))


class TransactionTests(APITestCase):
    def setUp(self):
        self.auth_utils = AuthenticationUtils(self.client)
        self.user_id = self.auth_utils.user_login()

        TransactionFactory.create_batch(10, user_id=1)
        self.url = reverse('budget:transaction-list')

    def test_list(self):
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 10)

    def test_list_summary(self):
        url = reverse('budget:transaction-by-month')
        response = self.client.get(url + '?month=' + '2021-02', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add(self):
        cat = CategoryFactory()
        data = {
            'category': cat.id,
            'amount': '10.00',
            'direction': DIRECTION.income,
        }
        response = self.client.post(self.url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_transaction_at(self):
        cat = CategoryFactory()
        data = {
            'category': cat.id,
            'amount': '10.00',
            'direction': DIRECTION.income,
            'transaction_at': '2021-01-02T00:00:00',
            'wallet': 0,
        }
        response = self.client.post(self.url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update(self):
        obj = TransactionFactory(user_id=self.user_id)
        url = reverse('budget:transaction-list')
        data = {
            'category': obj.category_id,
            'amount': '20.00',
            'direction': obj.direction,
        }
        response = self.client.put(url + '{}/'.format(obj.id), data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete(self):
        obj = TransactionFactory(user_id=self.user_id)
        url = reverse('budget:transaction-list')
        response = self.client.delete(url + '{}/'.format(obj.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class TransactionFilterTests(APITestCase):
    def setUp(self):
        self.auth_utils = AuthenticationUtils(self.client)
        self.user_id = self.auth_utils.user_login()
        self.url = reverse('budget:transaction-list')

    def test_filter_direction(self):
        TransactionFactory.create_batch(5, user_id=1, direction=DIRECTION.income)
        TransactionFactory.create_batch(5, user_id=1, direction=DIRECTION.expense)
        response = self.client.get(self.url + '?direction=' + DIRECTION.income, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 5)

    def test_filter_wallet(self):
        wallet = WalletFactory(user_id=self.user_id)
        TransactionFactory.create_batch(5, user_id=1, wallet=wallet)
        TransactionFactory.create_batch(5, user_id=1)
        response = self.client.get(self.url + '?wallet=' + str(wallet.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 5)

        response = self.client.get(self.url + '?wallet=0', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 5)

    def test_by_month_filter(self):
        TransactionFactory.create_batch(5, user_id=1, transaction_at=datetime(2021, 2, 20))

        url = reverse('budget:transaction-by-month')
        response = self.client.get(url + '?month=2021-02', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.json()[0]['expense_amount']), Decimal(50))

    def test_by_month_filter_wallet(self):
        wallet = WalletFactory(user_id=self.user_id)
        TransactionFactory.create_batch(5, user_id=1, transaction_at=datetime(2021, 2, 20), wallet=wallet)
        TransactionFactory.create_batch(5, user_id=1, transaction_at=datetime(2021, 2, 20))
        url = reverse('budget:transaction-by-month')
        response = self.client.get(url + '?month=2021-02' + '&wallet=' + str(wallet.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.json()[0]['expense_amount']), Decimal(50))
        response = self.client.get(url + '?month=2021-02' + '&wallet=0', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.json()[0]['expense_amount']), Decimal(50))

    def test_month_summary_filter(self):
        # +50
        TransactionFactory.create_batch(5, user_id=1, transaction_at=datetime(2021, 1, 1), direction=DIRECTION.income)
        # -20
        TransactionFactory.create_batch(2, user_id=1, transaction_at=datetime(2021, 1, 1), direction=DIRECTION.expense)
        # +30
        TransactionFactory.create_batch(3, user_id=1, transaction_at=datetime(2021, 2, 1), direction=DIRECTION.income)
        # -10
        TransactionFactory.create_batch(1, user_id=1, transaction_at=datetime(2021, 2, 1), direction=DIRECTION.expense)

        url = reverse('budget:transaction-month-summary')
        response = self.client.get(url + '?month=2021-02', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(Decimal(data['income_amount']), Decimal(30))
        self.assertEqual(Decimal(data['expense_amount']), Decimal(10))
        self.assertEqual(Decimal(data['current_balance']), Decimal(20))
        self.assertEqual(Decimal(data['previous_balance']), Decimal(30))
        self.assertEqual(Decimal(data['balance']), Decimal(50))

    def test_by_month_summary_wallet(self):
        wallet = WalletFactory(user_id=self.user_id)
        # +50
        TransactionFactory.create_batch(5, user_id=1, transaction_at=datetime(2021, 1, 1),
                                        direction=DIRECTION.income, wallet=wallet)
        # -20
        TransactionFactory.create_batch(2, user_id=1, transaction_at=datetime(2021, 1, 1),
                                        direction=DIRECTION.expense, wallet=wallet)
        # +30
        TransactionFactory.create_batch(3, user_id=1, transaction_at=datetime(2021, 2, 1),
                                        direction=DIRECTION.income, wallet=wallet)
        # -10
        TransactionFactory.create_batch(1, user_id=1, transaction_at=datetime(2021, 2, 1),
                                        direction=DIRECTION.expense, wallet=wallet)

        # +20
        TransactionFactory.create_batch(2, user_id=1, transaction_at=datetime(2021, 1, 1),
                                        direction=DIRECTION.income)
        # -10
        TransactionFactory.create_batch(1, user_id=1, transaction_at=datetime(2021, 1, 1),
                                        direction=DIRECTION.expense)
        # +40
        TransactionFactory.create_batch(4, user_id=1, transaction_at=datetime(2021, 2, 1),
                                        direction=DIRECTION.income)
        # -20
        TransactionFactory.create_batch(2, user_id=1, transaction_at=datetime(2021, 2, 1),
                                        direction=DIRECTION.expense)

        url = reverse('budget:transaction-month-summary')
        response = self.client.get(url + '?month=2021-02' + '&wallet=' + str(wallet.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(Decimal(data['income_amount']), Decimal(30))
        self.assertEqual(Decimal(data['expense_amount']), Decimal(10))
        self.assertEqual(Decimal(data['current_balance']), Decimal(20))
        self.assertEqual(Decimal(data['previous_balance']), Decimal(30))
        self.assertEqual(Decimal(data['balance']), Decimal(50))

        response = self.client.get(url + '?month=2021-02' + '&wallet=0', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(Decimal(data['income_amount']), Decimal(40))
        self.assertEqual(Decimal(data['expense_amount']), Decimal(20))
        self.assertEqual(Decimal(data['current_balance']), Decimal(20))
        self.assertEqual(Decimal(data['previous_balance']), Decimal(10))
        self.assertEqual(Decimal(data['balance']), Decimal(30))
