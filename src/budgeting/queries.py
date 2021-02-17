from budgeting.models import TransactionByDay


class TransactionQueries:
    @staticmethod
    def get_transaction_by_month(user_id, month):
        qs = TransactionByDay.objects.raw('''select t.user_id as id, 
       t.user_id,
       sum(if(t.direction = 'expense', t.amount, 0)) as expense_amount,
       sum(if(t.direction = 'income', t.amount, 0)) as income_amount,
       date(t.created_at) as created_at
from budgeting_transaction t
where 1=1
and DATE_FORMAT(t.created_at, '%%Y-%%m') = %s
and t.user_id = %s
group by t.user_id, date(t.created_at)
''', (month, user_id))

        return qs
