from decimal import Decimal

from django.db import connection

from budgeting.models import TransactionByDay, WalletBalance, TransactionByCategory
from common.business import build_month_table


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
    def get_transaction_summary_by_category(user_id: int, t: str, direction: str, month: str,
                                            wallet_id: int = None):
        wallet_cond = ''
        if wallet_id:
            if wallet_id == '0':
                wallet_cond = 'and t.wallet_id is null'
            else:
                wallet_cond = 'and t.wallet_id = %(wallet_id)s'
        dt_cond = ''
        if t == 'month':
            dt_cond = "and DATE_FORMAT(t.transaction_at, '%%Y-%%m') = %(month)s"
        elif t == 'year':
            dt_cond = "and DATE_FORMAT(t.transaction_at, '%%Y') = %(month)s"

        txt = '''
select bc.id as id, bc.id as category_id, bc.code as category_code, bc.name as category_name, 
    sum(t.amount) as amount
from budgeting_transaction t
join budgeting_category bc on t.category_id = bc.id
where 1=1
and t.user_id = %(user_id)s
and t.direction = %(direction)s
{dt_cond}
{wallet_cond}
group by bc.id, bc.code, bc.name
order by sum(t.amount) desc
'''.format(wallet_cond=wallet_cond, dt_cond=dt_cond)

        qs = TransactionByCategory.objects.raw(txt, {
            'month': month, 'user_id': user_id, 'direction': direction, 'wallet_id': wallet_id
        })

        return qs

    @staticmethod
    def get_transaction_summary_category_by_month(user_id: int, category_id: int,
                                                  from_month: str, to_month: str,
                                                  wallet_id: int = None):
        month_table = build_month_table(from_month, to_month)
        wallet_cond = ''
        if wallet_id:
            if wallet_id == '0':
                wallet_cond = 'and t.wallet_id is null'
            else:
                wallet_cond = 'and t.wallet_id = %(wallet_id)s'

        txt = '''
select dt.mth,
    sum(coalesce(t.amount, 0)) as amount
from (
{month_table}
    ) as dt
left join budgeting_transaction t on dt.mth = DATE_FORMAT(t.transaction_at, '%%Y-%%m') 
                                         and t.user_id = %(user_id)s
                                         and t.category_id = %(category_id)s
                                         {wallet_cond}
where 1=1
group by dt.mth
order by dt.mth;
'''.format(wallet_cond=wallet_cond, month_table=month_table)

        result = []
        with connection.cursor() as cursor:
            cursor.execute(txt, {
                'user_id': user_id,
                'wallet_id': wallet_id,
                'category_id': category_id
            })
            rows = cursor.fetchall()
            for row in rows:
                result.append({
                    'month': row[0],
                    'amount': Decimal(row[1])
                })

        return result


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
select r1.id, r1.user_id, r1.wallet_id, r1.plaid_id, r1.name, r1.sub_name, r1.type, 
       sum(r1.income_amount) as income_amount, sum(r1.expense_amount) as expense_amount, sum(r1.balance) as balance
from
(
    select t.user_id as id,
           t.user_id,
           0 as wallet_id,
           0 as plaid_id,
           'Manual Wallet' as `name`,
           '' as `sub_name`,
           'manual_wallet' as `type`,
           sum(if(t.direction = 'income', t.amount, 0)) as income_amount,
           sum(if(t.direction = 'expense', t.amount, 0)) as expense_amount,
           sum(if(t.direction = 'income', t.amount, 0)) - sum(if(t.direction = 'expense', t.amount, 0)) as balance
    from budgeting_transaction t
    where 1=1
    and t.wallet_id is null
    and t.user_id = %(user_id)s
    group by t.user_id
    union all
    select %(user_id)s as id,
           %(user_id)s as user_id,
           0 as wallet_id,
           0 as plaid_id,
           'Manual Wallet' as name,
           '' as sub_name,
           'manual_wallet' as type,
           0 as income_amount,
           0 as expense_amount,
           0 as balance
) as r1
group by r1.id, r1.user_id, r1.wallet_id, r1.plaid_id, r1.name, r1.sub_name, r1.type
union all
select r2.id, r2.user_id, r2.wallet_id, r2.plaid_id, r2.name, r2.sub_name, r2.type, 
       sum(r2.income_amount) as income_amount, sum(r2.expense_amount) as expense_amount, sum(r2.balance) as balance
from
(
    select t.user_id as id,
           t.user_id,
           null as wallet_id,
           0 as plaid_id,
           'Total Wallet' as `name`,
           '' as `sub_name`,
           'total_wallet' as `type`,
           sum(if(t.direction = 'income', t.amount, 0)) as income_amount,
           sum(if(t.direction = 'expense', t.amount, 0)) as expense_amount,
           sum(if(t.direction = 'income', t.amount, 0)) - sum(if(t.direction = 'expense', t.amount, 0)) as balance
    from budgeting_transaction t
    where 1=1
    and t.user_id = %(user_id)s
    group by t.user_id
    union all
    select %(user_id)s as id,
           %(user_id)s as user_id,
           null as wallet_id,
           0 as plaid_id,
           'Total Wallet' as name,
           '' as sub_name,
           'total_wallet' as type,
           0 as income_amount,
           0 as expense_amount,
           0 as balance
) as r2
group by r2.id, r2.user_id, r2.wallet_id, r2.plaid_id, r2.name, r2.sub_name, r2.type
) as r order by r.wallet_id;
'''

        qs = WalletBalance.objects.raw(txt, {'user_id': user_id})
        return qs


class BudgetQueries:
    @staticmethod
    def get_budget_details(user_id: int, wallet_id: int, category_id: int,
                           is_over: bool = None, is_end: bool = None):
        return None
