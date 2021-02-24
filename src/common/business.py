import random
import string
from collections import OrderedDict
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from dateutil.relativedelta import relativedelta
from django.utils import timezone


def get_now():
    now = timezone.now()
    # if not timezone.is_naive(now):
    #     now = timezone.make_naive(now, timezone.utc)

    return now


def generate_random_code(n: int):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))


def generate_random_code_2(n: int):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))


def generate_random_digit(n: int):
    return ''.join(random.choices(string.digits, k=n))


def round_currency(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal('.01'), ROUND_HALF_UP)


def round_crypto(amount: Decimal, decimal_place=6) -> Decimal:
    return amount.quantize(Decimal('.{}1'.format('0' * (decimal_place - 1))), ROUND_HALF_UP)


def build_month_table(from_month: str, to_month: str):
    from_date = datetime.strptime(from_month + '-01', '%Y-%m-%d')
    to_date = datetime.strptime(to_month + '-01', '%Y-%m-%d')
    cur_date = from_date
    dt_strs = []
    while cur_date <= to_date:
        dt_strs.append("select '{}' as mth ".format(cur_date.strftime('%Y-%m')))
        cur_date += relativedelta(months=1)
    dt_str = 'union all '.join(dt_strs)
    return dt_str
