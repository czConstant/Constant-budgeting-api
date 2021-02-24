import json
from datetime import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property

from budgeting.constants import DIRECTION
from constant_core.business import ConstantCoreBusiness
from constant_core.models import User as CoreUser


class ConstUser(User):
    class Meta:
        managed = False

    user_id = models.IntegerField()
    token = models.TextField()

    @staticmethod
    def from_user(user: CoreUser):
        return ConstUser(
            user_id=user.id,
            email=user.email
        )

    @cached_property
    def get_db_user(self) -> CoreUser:
        return ConstantCoreBusiness.get_user(self.user_id)

    @property
    def c_first_name(self):
        return self.get_db_user.first_name

    @property
    def c_middle_name(self):
        return self.get_db_user.middle_name

    @property
    def c_last_name(self):
        return self.get_db_user.last_name

    @property
    def role_id(self) -> int:
        return self.get_db_user.user_role_id

    @property
    def full_name(self) -> str:
        return self.get_db_user.full_name

    @property
    def dob(self) -> str:
        return self.get_db_user.dob

    @property
    def phone_number(self) -> str:
        return self.get_db_user.phone_number

    @property
    def verified_level(self) -> int:
        return self.get_db_user.verified_level

    @property
    def constant_balance(self) -> Decimal:
        return self.get_db_user.constant_balance_friendly

    @property
    def constant_balance_holding(self) -> Decimal:
        return self.get_db_user.constant_balance_holding_friendly

    @property
    def pro_saving_user(self) -> bool:
        return self.get_db_user.pro_saving_user

    @property
    def agent_user(self) -> bool:
        return self.get_db_user.agent_user

    @property
    def lo_user(self) -> bool:
        return self.get_db_user.lo_user

    @property
    def language(self) -> str:
        return self.get_db_user.language

    @property
    def white_label(self) -> bool:
        return self.get_db_user.white_label

    @property
    def permissions(self) -> str:
        return self.get_db_user.permissions

    @property
    def membership(self) -> int:
        return self.get_db_user.membership

    @property
    def withdraw_confirmed_email_on(self) -> bool:
        return self.get_db_user.withdraw_confirmed_email_on

    @property
    def is_kyc(self) -> bool:
        return self.verified_level in (6, 7)

    @property
    def tax_country(self) -> str:
        return self.get_db_user.tax_country

    @property
    def suspend_withdrawal_to(self) -> datetime:
        return self.get_db_user.suspend_withdrawal_to

    @property
    def account_type(self) -> int:
        return self.get_db_user.account_type

    @property
    def internal_user(self) -> bool:
        return self.get_db_user.internal_user

    def build_dict(self) -> dict:
        return {
            'full_name': self.full_name,
            'email': self.email,
            'balance': '{:.2f}'.format(self.constant_balance)
        }


class SystemConstUser(ConstUser):
    class Meta:
        managed = False
        proxy = True

    @property
    def role_id(self) -> int:
        return 999

    @property
    def full_name(self) -> str:
        return 'admin'

    @property
    def dob(self) -> str:
        return ''

    @property
    def phone_number(self) -> str:
        return ''

    @property
    def verified_level(self) -> int:
        return 999

    @property
    def constant_balance(self) -> Decimal:
        return Decimal(0)

    @property
    def constant_balance_holding(self) -> Decimal:
        return Decimal(0)

    @property
    def pro_saving_user(self) -> bool:
        return False

    @property
    def agent_user(self) -> bool:
        return False

    @property
    def language(self) -> str:
        return 'en'

    @property
    def white_label(self) -> bool:
        return False

    @property
    def permissions(self) -> str:
        return ''

    @property
    def membership(self) -> int:
        return 0


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CategoryGroup(TimestampedModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True, default='')
    order = models.IntegerField(default=0)
    deleted_at = models.DateTimeField(null=True)


class Category(TimestampedModel):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True, blank=True)
    code = models.CharField(max_length=50)
    direction = models.CharField(max_length=50, choices=DIRECTION, default=DIRECTION.income)
    order = models.IntegerField(default=0)
    deleted_at = models.DateTimeField(null=True)
    group = models.ForeignKey(CategoryGroup, related_name='group_categories', null=True, on_delete=models.SET_NULL)
    user_id = models.IntegerField(null=True)

    DEFAULT_CODE = 'others'
    MANUAL_CODE = 'manual'


class CategoryMapping(TimestampedModel):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, related_name='category_mappings', on_delete=models.CASCADE)


class Wallet(TimestampedModel):
    user_id = models.IntegerField()
    name = models.CharField(max_length=255, null=True, blank=True)
    sub_name = models.CharField(max_length=255, null=True, blank=True)
    plaid_id = models.IntegerField(null=True)
    last_import = models.DateField(default=timezone.now)
    error = models.CharField(max_length=255, null=True, blank=True)
    error_details = models.TextField(null=True, blank=True)
    error_at = models.DateTimeField(null=True)
    deleted_at = models.DateTimeField(null=True)


class Transaction(TimestampedModel):
    user_id = models.IntegerField()
    category = models.ForeignKey(Category,
                                 related_name='category_transactions',
                                 on_delete=models.SET_NULL, null=True)
    category_text = models.CharField(max_length=255, null=True, blank=True)
    direction = models.CharField(max_length=50, choices=DIRECTION)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    note = models.CharField(max_length=255, null=True, blank=True)
    wallet = models.ForeignKey(Wallet,
                               related_name='wallet_transactions',
                               on_delete=models.SET_NULL, null=True)
    transaction_at = models.DateTimeField(null=True, default=timezone.now)
    external_id = models.CharField(max_length=255, null=True, blank=True)
    detail = models.TextField(null=True, blank=True)

    @cached_property
    def detail_dict(self):
        try:
            return json.loads(self.detail)
        except:
            return {}


class TransactionByDay(models.Model):
    class Meta:
        managed = False
    user_id = models.IntegerField()
    income_amount = models.DecimalField(max_digits=18, decimal_places=2)
    expense_amount = models.DecimalField(max_digits=18, decimal_places=2)
    transaction_at = models.DateField()


class TransactionByCategory(models.Model):
    class Meta:
        managed = False
    user_id = models.IntegerField()
    direction = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    category_id = models.IntegerField()
    category_code = models.CharField(max_length=255)
    category_name = models.CharField(max_length=255)


class WalletBalance(models.Model):
    class Meta:
        managed = False

    user_id = models.IntegerField()
    wallet_id = models.IntegerField()
    plaid_id = models.IntegerField()
    name = models.CharField(max_length=255)
    sub_name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    income_amount = models.DecimalField(max_digits=18, decimal_places=2)
    expense_amount = models.DecimalField(max_digits=18, decimal_places=2)
    balance = models.DecimalField(max_digits=18, decimal_places=2)
