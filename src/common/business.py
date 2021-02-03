import random
import string
from decimal import Decimal, ROUND_HALF_UP

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
