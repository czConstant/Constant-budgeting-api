from django.db import connection

from budgeting.models import TransactionByDay, WalletBalance


class TransactionQueries:
    @staticmethod
    def get_transaction_by_month(user_id: int, month: str, wallet_id: int = None):
        wallet_cond = ''
        if wallet_id:
            if wallet_id == '0':
                wallet_cond = 'and t.wallet_id is null'
            else:
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

    @staticmethod
    def get_transaction_month_summary(user_id: int, month: str, wallet_id: int = None):
        wallet_cond = ''
        if wallet_id:
            if wallet_id == '0':
                wallet_cond = 'and t.wallet_id is null'
            else:
                wallet_cond = 'and t.wallet_id = %(wallet_id)s'

        txt = '''select t1.income, t1.expense, 
        coalesce(t1.balance, 0) as current_balance, 
        coalesce(t2.balance, 0) as previous_balance
from
(
select sum(if(t.direction = 'income', t.amount, 0)) - sum(if(t.direction = 'expense', t.amount, 0)) as balance, 
    sum(if(t.direction = 'income', t.amount, 0)) as income,
    sum(if(t.direction = 'expense', t.amount, 0)) as expense
from budgeting_transaction t
where 1=1
and DATE_FORMAT(t.transaction_at, '%%Y-%%m') = %(month)s
and t.user_id = %(user_id)s
{wallet_cond}
group by t.user_id
) t1,
(
select sum(if(t.direction = 'income', t.amount, 0)) - sum(if(t.direction = 'expense', t.amount, 0)) as balance
from budgeting_transaction t
where 1=1
and DATE_FORMAT(t.transaction_at, '%%Y-%%m') < %(month)s
and t.user_id = %(user_id)s
{wallet_cond}
group by t.user_id
) t2
'''.format(wallet_cond=wallet_cond)

        data = {
            'expense_amount': 0,
            'income_amount': 0,
            'current_balance': 0,
            'previous_balance': 0,
            'balance': 0,
        }
        with connection.cursor() as cursor:
            cursor.execute(txt, {'month': month, 'user_id': user_id, 'wallet_id': wallet_id})
            row = cursor.fetchone()
            if row:
                data['income_amount'] = row[0]
                data['expense_amount'] = row[1]
                data['current_balance'] = row[2]
                data['previous_balance'] = row[3]
                data['balance'] = data['previous_balance'] + data['current_balance']

        return data


class WalletQueries:
    @staticmethod
    def wallet_balance(user_id: int):
        txt = '''
select *
from(
select t.user_id as id,
       t.user_id,
       t.wallet_id,
       bw.name,
       'linked_bank' as `type`,
       sum(if(t.direction = 'income', t.amount, 0)) as income_amount,
       sum(if(t.direction = 'expense', t.amount, 0)) as expense_amount,
       sum(if(t.direction = 'income', t.amount, 0)) - sum(if(t.direction = 'expense', t.amount, 0)) as balance
from budgeting_transaction t
join budgeting_wallet bw on t.wallet_id = bw.id
where 1=1
and t.wallet_id is not null
and t.user_id = %(user_id)s
group by t.user_id, t.wallet_id
union all
select t.user_id as id,
       t.user_id,
       0 as wallet_id,
       'Total Wallet',
       'total_wallet' as `type`,
       sum(if(t.direction = 'income', t.amount, 0)) as income_amount,
       sum(if(t.direction = 'expense', t.amount, 0)) as expense_amount,
       sum(if(t.direction = 'income', t.amount, 0)) - sum(if(t.direction = 'expense', t.amount, 0)) as balance
from budgeting_transaction t
where 1=1
and t.wallet_id is null
and t.user_id = %(user_id)s
group by t.user_id
) as r order by r.wallet_id;
'''

        qs = WalletBalance.objects.raw(txt, {'user_id': user_id})
        return qs
