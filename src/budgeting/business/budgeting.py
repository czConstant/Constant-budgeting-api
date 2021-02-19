import json
import logging
from datetime import timedelta
from decimal import Decimal

from django.core.serializers.json import DjangoJSONEncoder

from budgeting.constants import DIRECTION
from budgeting.models import Transaction, Wallet, Category, CategoryMapping
from common.business import get_now
from constant_core.business import ConstantCoreBusiness
from integration_3rdparty.plaid import PlaidManagement


class TransactionBusiness:
    @staticmethod
    def import_transaction_from_plaid(user_id: int, wallet: Wallet, from_date=None, to_date=None):
        from_date = from_date.strftime('%Y-%m-%d') if from_date else get_now().strftime('%Y-%m-%d')
        to_date = to_date.strftime('%Y-%m-%d') if to_date else (get_now() + timedelta(days=1)).strftime('%Y-%m-%d')

        plaid_account = ConstantCoreBusiness.get_plaid_account(wallet.plaid_id)
        transactions = PlaidManagement.get_transaction(plaid_account.access_token, from_date, to_date)

        default_category = 'others'
        cache_category_mapping = {
            DIRECTION.income: {
                default_category: Category.objects.get(code=default_category, direction=DIRECTION.income)
            },
            DIRECTION.expense: {
                default_category: Category.objects.get(code=default_category, direction=DIRECTION.expense)
            }
        }

        for transaction in transactions:
            try:
                amount = Decimal(transaction['amount'])
                direction = DIRECTION.income if amount < 0 else DIRECTION.expense
                location = transaction.get('location')
                location = {} if not location else location
                note = '{name}, {address}, {city}, {region} {postal_code} {country}'.format(
                    name=transaction.get('name'),
                    address=location.get('address'),
                    city=location.get('city'),
                    region=location.get('region'),
                    postal_code=location.get('postal_code'),
                    country=location.get('country'),
                )
                picked_cat = None
                cats = transaction.get('category', [])
                cats = cats if cats else []
                if cats:
                    cats.sort(key=lambda item: len(item), reverse=True)
                    picked_cat_txt = cats[0]
                    if picked_cat_txt not in cache_category_mapping:
                        obj = CategoryMapping.objects.filter(name=picked_cat_txt).first()
                        if obj:
                            cache_category_mapping[picked_cat_txt] = obj
                    if picked_cat_txt in cache_category_mapping:
                        picked_cat = cache_category_mapping[picked_cat_txt]
                    else:
                        picked_cat = cache_category_mapping[default_category]

                Transaction.objects.create(
                    user_id=user_id,
                    amount=amount,
                    direction=direction,
                    note=note,
                    wallet=wallet,
                    transaction_at=location['authorized_date'],
                    detail=json.dumps(transaction, cls=DjangoJSONEncoder),
                    category=picked_cat,
                    category_text=','.join(cats)
                )
            except Exception as ex:
                logging.exception(ex)
