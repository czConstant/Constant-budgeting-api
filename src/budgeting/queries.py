from budgeting.models import TransactionByDay


class TransactionQueries:
    @staticmethod
    def get_transaction_by_month(user_id: int, month: str, wallet_id: int = None):
        wallet_cond = ''
        if wallet_id:
            wallet_cond = 'and t.wallet_id = %(wallet_id)s'

        txt = '''select t.user_id as id, 
       t.user_id,
       sum(if(t.direction = 'expense', t.amount, 0)) as expense_amount,
       sum(if(t.direction = 'income', t.amount, 0)) as income_amount,
       date(t.transaction_at) as transaction_at
from budgeting_transaction t
where 1=1
and DATE_FORMAT(t.transaction_at, '%%Y-%%m') = %(month)s
and t.user_id = %(user_id)s
{wallet_cond}
group by t.user_id, date(t.transaction_at)
'''.format(wallet_cond=wallet_cond)

        qs = TransactionByDay.objects.raw(txt, {'month': month, 'user_id': user_id, 'wallet_id': wallet_id})

        return qs
