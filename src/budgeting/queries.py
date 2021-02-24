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
    def get_transaction_summary(user_id: int, t: str, month: str, wallet_id: int = None):
        wallet_cond = ''
        if wallet_id:
            if wallet_id == '0':
                wallet_cond = 'and t.wallet_id is null'
            else:
                wallet_cond = 'and t.wallet_id = %(wallet_id)s'
        dt_cond = ''
        prev_dt_cond = 'and 0=1'
        if t == 'month':
            dt_cond = "and DATE_FORMAT(t.transaction_at, '%%Y-%%m') = %(month)s"
            prev_dt_cond = "and DATE_FORMAT(t.transaction_at, '%%Y-%%m') < %(month)s"
        elif t == 'year':
            dt_cond = "and DATE_FORMAT(t.transaction_at, '%%Y') = %(month)s"
            prev_dt_cond = "and DATE_FORMAT(t.transaction_at, '%%Y') < %(month)s"

        txt1 = '''select
    sum(if(t.direction = 'income', t.amount, 0)) as income,
    sum(if(t.direction = 'expense', t.amount, 0)) as expense,
    sum(if(t.direction = 'income', t.amount, 0)) - sum(if(t.direction = 'expense', t.amount, 0)) as balance
from budgeting_transaction t
where 1=1
and t.user_id = %(user_id)s
{dt_cond}
{wallet_cond}
group by t.user_id
'''.format(wallet_cond=wallet_cond,
           dt_cond=dt_cond)

        txt2 = '''select sum(if(t.direction = 'income', t.amount, 0)) - sum(if(t.direction = 'expense', t.amount, 0)) as balance
from budgeting_transaction t
where 1=1
and t.user_id = %(user_id)s
{prev_dt_cond}
{wallet_cond}
group by t.user_id
'''.format(wallet_cond=wallet_cond,
           prev_dt_cond=prev_dt_cond)

        data = {
            'expense_amount': 0,
            'income_amount': 0,
            'current_balance': 0,
            'previous_balance': 0,
            'balance': 0,
        }
        with connection.cursor() as cursor:
            cursor.execute(txt1, {'month': month, 'user_id': user_id, 'wallet_id': wallet_id})
            row = cursor.fetchone()
            if row:
                data['income_amount'] = row[0]
                data['expense_amount'] = row[1]
                data['current_balance'] = row[2]
            cursor.execute(txt2, {'month': month, 'user_id': user_id, 'wallet_id': wallet_id})
            row = cursor.fetchone()
            if row:
                data['previous_balance'] = row[0]
            data['balance'] = data['previous_balance'] + data['current_balance']

        return data

    @staticmethod
    def get_transaction_month_report(user_id: int, month: str, direction: str, wallet_id: int = None):
        wallet_cond = ''
        if wallet_id:
            if wallet_id == '0':
                wallet_cond = 'and t.wallet_id is null'
            else:
                wallet_cond = 'and t.wallet_id = %(wallet_id)s'

        txt = '''
'''.format(wallet_cond=wallet_cond)

        with connection.cursor() as cursor:
            cursor.execute(txt, {'month': month, 'user_id': user_id, 'wallet_id': wallet_id})

class WalletQueries:
    @staticmethod
    def wallet_balance(user_id: int):
        txt = '''
select *
from(
select bw.user_id as id,
       bw.user_id,
       bw.id as wallet_id,
       bw.plaid_id as plaid_id,
       bw.name,
       bw.sub_name,
       'linked_bank' as `type`,
       sum(if(t.direction = 'income', t.amount, 0)) as income_amount,
       sum(if(t.direction = 'expense', t.amount, 0)) as expense_amount,
       sum(if(t.direction = 'income', t.amount, 0)) - sum(if(t.direction = 'expense', t.amount, 0)) as balance
from budgeting_wallet bw
left join budgeting_transaction t on t.wallet_id = bw.id
where 1=1
and bw.deleted_at is null
and bw.user_id = %(user_id)s
group by bw.user_id, bw.id, bw.plaid_id
union all
select t.user_id as id,
       t.user_id,
       0 as wallet_id,
       0 as plaid_id,
       'Total Wallet' as `name`,
       '' as `sub_name`,
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
