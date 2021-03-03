import json
import logging
from datetime import timedelta
from decimal import Decimal

from django.core.serializers.json import DjangoJSONEncoder

from budgeting.business.category import CategoryBusiness
from budgeting.business.wallet import WalletBusiness
from budgeting.constants import DIRECTION
from budgeting.models import Transaction, Wallet, Category
from common.business import get_now
from constant_core.business import ConstantCoreBusiness
from integration_3rdparty.plaid import PlaidManagement


class TransactionBusiness:
    @staticmethod
    def import_transaction_from_plaid(user_id: int, wallet: Wallet, from_date=None, to_date=None):
        from_date = from_date.strftime('%Y-%m-%d') if from_date else get_now().strftime('%Y-%m-%d')
        to_date = to_date.strftime('%Y-%m-%d') if to_date else (get_now() + timedelta(days=1)).strftime('%Y-%m-%d')

        plaid_account = ConstantCoreBusiness.get_plaid_account(wallet.plaid_id)
        if not plaid_account:
            WalletBusiness.delete_wallet(wallet)
            
        transactions = PlaidManagement.get_transaction(plaid_account.access_token, from_date, to_date)

        default_category = Category.DEFAULT_CODE
        cache_category_mapping = CategoryBusiness.load_category_mapping()

        for transaction in transactions:
            try:
                amount = Decimal(transaction['amount'])
                direction = DIRECTION.income if amount < 0 else DIRECTION.expense
                amount = amount * Decimal(-1) if amount < 0 else amount
                note = '{}'.format(transaction.get('name'))
                picked_cat = None
                cats = transaction.get('category', [])
                cats = cats if cats else []
                if cats:
                    cats.reverse()
                    for cat in cats:
                        if cat in cache_category_mapping[direction]:
                            picked_cat = cache_category_mapping[direction][cat]
                            break
                    else:
                        picked_cat = cache_category_mapping[direction][default_category]

                obj, created = Transaction.objects.get_or_create(
                    user_id=user_id,
                    amount=amount,
                    currency=transaction['iso_currency_code'],
                    direction=direction,
                    external_id=transaction['transaction_id'],
                    wallet=wallet,
                    defaults={
                        'note': note,
                        'transaction_at': transaction['date'],
                        'detail': json.dumps(transaction, cls=DjangoJSONEncoder),
                        'category': picked_cat,
                        'category_text': ','.join(cats),
                    }
                )
                if not created:
                    if obj.category_id and obj.category_id != picked_cat.id:
                        obj.category = picked_cat
                        obj.save()
            except Exception as ex:
                logging.exception(ex)
