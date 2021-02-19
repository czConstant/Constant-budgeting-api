from decimal import Decimal

import factory

from budgeting.constants import DIRECTION


class CategoryGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'budgeting.CategoryGroup'

    name = 'Category Group'


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'budgeting.Category'

    name = 'Category'
    description = 'Description'
    code = 'code'


class TransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'budgeting.Transaction'

    user_id = factory.Sequence(lambda n: n)
    direction = DIRECTION.expense
    amount = Decimal(10)


class WalletFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'budgeting.Wallet'

    user_id = factory.Sequence(lambda n: n)
    name = 'Wallet'
