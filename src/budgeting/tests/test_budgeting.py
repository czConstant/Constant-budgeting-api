from datetime import datetime
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from budgeting.constants import DIRECTION
from budgeting.factories import CategoryFactory, TransactionFactory, WalletFactory, CategoryGroupFactory
from budgeting.models import Transaction, Wallet, Category
from common.business import get_now
from common.test_mocks import CoreMock
from common.test_utils import AuthenticationUtils


class CategoryGroupTests(APITestCase):
    def setUp(self):
        self.auth_utils = AuthenticationUtils(self.client)
        self.user_id = self.auth_utils.user_login()

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
        self.auth_utils = AuthenticationUtils(self.client)
        self.user_id = self.auth_utils.user_login()

        CategoryFactory.create_batch(10)
        self.url = reverse('budget:category-list')

    def test_list(self):
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 10)

    def test_add(self):
        group_1 = CategoryGroupFactory(name='Group 1')
        data = {
            'name': 'Manual Category',
            'direction': DIRECTION.income,
            'description': 'Description',
            'group': group_1.id
        }
        response = self.client.post(self.url, data=data, format='json')
        resp = response.json()
        cat = Category.objects.get(id=resp['id'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(cat.user_id, self.user_id)
        self.assertEqual(cat.code, Category.MANUAL_CODE)

    def test_update(self):
        group_1 = CategoryGroupFactory(name='Group 1')
        group_2 = CategoryGroupFactory(name='Group 2')
        cat = CategoryFactory(user_id=self.user_id, direction=DIRECTION.income, group=group_1)
        data = {
            'name': 'New Name',
            'direction': DIRECTION.expense,
            'description': 'New Description',
            'group': group_2.id
        }
        response = self.client.put(self.url + '{}/'.format(cat.id), data=data, format='json')
        new_cat = Category.objects.get(id=cat.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(new_cat.name, 'New Name')
        self.assertEqual(new_cat.direction, DIRECTION.expense)
        self.assertEqual(new_cat.code, Category.MANUAL_CODE)

    def test_delete(self):
        group_1 = CategoryGroupFactory(name='Group 1')
        # Default category
        CategoryFactory(user_id=self.user_id, direction=DIRECTION.income, code=Category.DEFAULT_CODE)

        cat = CategoryFactory(user_id=self.user_id, direction=DIRECTION.income, group=group_1)
        tx = TransactionFactory(user_id=self.user_id, transaction_at=datetime(2021, 1, 1),
                                direction=DIRECTION.income, category=cat)

        response = self.client.delete(self.url + '{}/'.format(cat.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        new_tx = Transaction.objects.get(id=tx.id)
        self.assertEqual(new_tx.category.code, Category.DEFAULT_CODE)


class WalletTests(APITestCase):
    def setUp(self):
        self.auth_utils = AuthenticationUtils(self.client)
        self.user_id = self.auth_utils.user_login()
        WalletFactory.create_batch(10, user_id=self.user_id)
        self.url = reverse('budget:wallet-list')

        self.core_mock = CoreMock()

    def test_list(self):
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Wallet number 0
        self.assertEqual(len(response.json()), 10 + 1)

    def test_add(self):
        self.core_mock.get_plaid_account()
        data = {
            'plaid_id': 1
        }
        response = self.client.post(self.url, data=data, format='json')
        resp = response.json()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        w = Wallet.objects.get(id=resp['id'])
        self.assertEqual(w.name, 'Plaid (savings)')
        self.assertEqual(w.plaid_id, 1)

    def test_add_after_delete(self):
        WalletFactory(user_id=self.user_id, deleted_at=get_now(), name='Deleted', plaid_id=2)
        self.core_mock.get_plaid_account(data={'id': 2})
        data = {
            'plaid_id': 2
        }
        response = self.client.post(self.url, data=data, format='json')
        resp = response.json()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        w = Wallet.objects.get(id=resp['id'])
        self.assertEqual(w.name, 'Deleted')
        self.assertEqual(w.plaid_id, 2)

    def test_delete(self):
        obj = WalletFactory(user_id=self.user_id, name='Deleted')

        response = self.client.delete(self.url + '{}/'.format(obj.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        w = Wallet.objects.get(id=obj.id)
        self.assertIsNone(obj.deleted_at)
        self.assertIsNotNone(w.deleted_at)

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

        for item in data:
            if item['wallet_id'] == wallet.id:
                self.assertEqual(Decimal(item['income_amount']), Decimal(80))
                self.assertEqual(Decimal(item['expense_amount']), Decimal(30))
                self.assertEqual(Decimal(item['balance']), Decimal(50))
            elif item['wallet_id'] == 0:
                self.assertEqual(Decimal(item['income_amount']), Decimal(60))
                self.assertEqual(Decimal(item['expense_amount']), Decimal(30))
                self.assertEqual(Decimal(item['balance']), Decimal(30))


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

    def test_add_default(self):
        cat = CategoryFactory(code='others', direction=DIRECTION.income)
        data = {
            'amount': '10.00',
            'direction': DIRECTION.income,
        }
        response = self.client.post(self.url, data=data, format='json')
        obj = Transaction.objects.get(id=response.json()['id'])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(obj.category_id, cat.id)

    def test_add_transaction_at(self):
        cat = CategoryFactory()
        data = {
            'category': cat.id,
            'amount': '10.00',
            'direction': DIRECTION.income,
            'transaction_at': '2021-01-02T00:00:00',
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

    def test_update_linked_bank(self):
        wallet = WalletFactory(user_id=self.user_id)
        obj = TransactionFactory(user_id=self.user_id, wallet=wallet)
        url = reverse('budget:transaction-list')
        data = {
            'category': obj.category_id,
            'amount': '20.00',
            'direction': DIRECTION.income,
            'note': 'Changed'
        }
        response = self.client.put(url + '{}/'.format(obj.id), data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_obj = Transaction.objects.get(id=obj.id)
        self.assertEqual(obj.direction, new_obj.direction)
        self.assertEqual(obj.amount, new_obj.amount)
        self.assertNotEqual(obj.note, new_obj.note)

    def test_delete(self):
        obj = TransactionFactory(user_id=self.user_id)
        url = reverse('budget:transaction-list')
        response = self.client.delete(url + '{}/'.format(obj.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_linked_bank(self):
        wallet = WalletFactory(user_id=self.user_id)
        obj = TransactionFactory(user_id=self.user_id, wallet=wallet)
        url = reverse('budget:transaction-list')
        response = self.client.delete(url + '{}/'.format(obj.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        new_obj = Transaction.objects.get(id=obj.id)
        # Cannot delete linked bank transaction
        self.assertEqual(obj.id, new_obj.id)


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
        response = self.client.get(self.url + '?wallet_id=' + str(wallet.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 5)

        response = self.client.get(self.url + '?wallet_id=0', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 5)

    def test_filter_cat(self):
        cat = CategoryFactory(code='cat1', direction=DIRECTION.expense)
        cat_default = CategoryFactory(code=Category.DEFAULT_CODE, direction=DIRECTION.income)
        TransactionFactory.create_batch(5, user_id=1, category=cat, direction=DIRECTION.expense)
        TransactionFactory.create_batch(5, user_id=1, category=cat_default, direction=DIRECTION.income)
        TransactionFactory.create_batch(5, user_id=1, category=None, direction=DIRECTION.income)
        response = self.client.get(self.url + '?category_id=' + str(cat.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 5)
        response = self.client.get(self.url + '?category_id=' + str(cat_default.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 10)

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
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
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

    def test_summary_filter_type_month(self):
        # +50
        TransactionFactory.create_batch(5, user_id=1, transaction_at=datetime(2021, 1, 1), direction=DIRECTION.income)
        # -20
        TransactionFactory.create_batch(2, user_id=1, transaction_at=datetime(2021, 1, 1), direction=DIRECTION.expense)
        # +30
        TransactionFactory.create_batch(3, user_id=1, transaction_at=datetime(2021, 2, 1), direction=DIRECTION.income)
        # -10
        TransactionFactory.create_batch(1, user_id=1, transaction_at=datetime(2021, 2, 1), direction=DIRECTION.expense)

        url = reverse('budget:transaction-summary')
        response = self.client.get(url + '?range=2021-02&type=month', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(Decimal(data['income_amount']), Decimal(30))
        self.assertEqual(Decimal(data['expense_amount']), Decimal(10))
        self.assertEqual(Decimal(data['current_balance']), Decimal(20))
        self.assertEqual(Decimal(data['previous_balance']), Decimal(30))
        self.assertEqual(Decimal(data['balance']), Decimal(50))

    def test_summary_filter_type_year(self):
        # +50
        TransactionFactory.create_batch(5, user_id=1, transaction_at=datetime(2021, 1, 1), direction=DIRECTION.income)
        # -20
        TransactionFactory.create_batch(2, user_id=1, transaction_at=datetime(2021, 1, 1), direction=DIRECTION.expense)
        # +30
        TransactionFactory.create_batch(3, user_id=1, transaction_at=datetime(2021, 2, 1), direction=DIRECTION.income)
        # -10
        TransactionFactory.create_batch(1, user_id=1, transaction_at=datetime(2021, 2, 1), direction=DIRECTION.expense)

        url = reverse('budget:transaction-summary')
        response = self.client.get(url + '?range=2021&type=year', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(Decimal(data['income_amount']), Decimal(80))
        self.assertEqual(Decimal(data['expense_amount']), Decimal(30))
        self.assertEqual(Decimal(data['current_balance']), Decimal(50))
        self.assertEqual(Decimal(data['previous_balance']), Decimal(0))
        self.assertEqual(Decimal(data['balance']), Decimal(50))

    def test_summary_by_category(self):
        cat1 = CategoryFactory(code='1')
        cat2 = CategoryFactory(code='2')
        cat3 = CategoryFactory(code='3')
        # +50
        TransactionFactory.create_batch(5, user_id=1, transaction_at=datetime(2021, 1, 1),
                                        direction=DIRECTION.income, category=cat1)
        # -20
        TransactionFactory.create_batch(2, user_id=1, transaction_at=datetime(2021, 1, 1),
                                        direction=DIRECTION.expense, category=cat2)
        # +30
        TransactionFactory.create_batch(3, user_id=1, transaction_at=datetime(2021, 2, 1),
                                        direction=DIRECTION.income, category=cat3)
        # -10
        TransactionFactory.create_batch(1, user_id=1, transaction_at=datetime(2021, 2, 1),
                                        direction=DIRECTION.expense, category=cat1)

        url = reverse('budget:transaction-summary-by-category')
        response = self.client.get(url + '?range=2021&type=year&wallet_id=0&direction=income', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(Decimal(data[0]['amount']), Decimal(50))
        self.assertEqual(data[0]['category_code'], '1')
        self.assertEqual(Decimal(data[1]['amount']), Decimal(30))
        self.assertEqual(data[1]['category_code'], '3')

        response = self.client.get(url + '?range=2021&type=year&wallet_id=0&direction=expense', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(Decimal(data[0]['amount']), Decimal(20))
        self.assertEqual(data[0]['category_code'], '2')
        self.assertEqual(Decimal(data[1]['amount']), Decimal(10))
        self.assertEqual(data[1]['category_code'], '1')
