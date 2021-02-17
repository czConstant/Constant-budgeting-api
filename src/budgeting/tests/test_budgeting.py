from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from budgeting.constants import DIRECTION
from budgeting.factories import CategoryFactory, TransactionFactory
from common.test_utils import AuthenticationUtils


class CategoryTests(APITestCase):
    def setUp(self):
        CategoryFactory.create_batch(10)
        self.url = reverse('budget:category-list')

    def test_list(self):
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['results']), 10)


class TransactionTests(APITestCase):
    def setUp(self):
        self.auth_utils = AuthenticationUtils(self.client)
        self.auth_utils.user_login()

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
