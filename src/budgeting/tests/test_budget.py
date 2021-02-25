from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from budgeting.factories import WalletFactory, CategoryFactory, BudgetFactory
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
