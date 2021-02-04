from decimal import Decimal

import factory

from budgeting.constants import DIRECTION


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'budgeting.Category'

    name = 'Name'
    description = 'Description'
    code = 'code'


class TransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'budgeting.Transaction'

    user_id = factory.Sequence(lambda n: n)
    direction = DIRECTION.expense
    amount = Decimal(10)
