from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property

from budgeting.constants import DIRECTION
from constant_core.models import User as CoreUser


class ConstUser(User):
    class Meta:
        managed = False

    user_id = models.IntegerField()
    token = models.TextField()
    company_id = models.IntegerField()  # Current working company

    @staticmethod
    def from_user(user: CoreUser):
        return ConstUser(
            user_id=user.id,
            email=user.email
        )

    @cached_property
    def get_db_user(self) -> CoreUser:
        return CoreUser.objects.get(id=self.user_id)

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
    def full_name(self) -> str:
        return '%s %s'.format(self.c_first_name, self.c_last_name)

    def build_dict(self) -> dict:
        return {
            'full_name': self.full_name,
            'email': self.email,
        }


class SystemConstUser(ConstUser):
    class Meta:
        managed = False
        proxy = True

    @cached_property
    def get_db_user(self) -> CoreUser:
        return CoreUser.objects.get(id=self.user_id)

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
    def full_name(self) -> str:
        return '%s %s'.format(self.c_first_name, self.c_last_name)


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CategoryGroup(TimestampedModel):
    name = models.CharField(max_length=255)
    order = models.IntegerField(default=0)
    deleted_at = models.DateTimeField(null=True)


class Category(TimestampedModel):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    direction = models.CharField(max_length=50, choices=DIRECTION, default=DIRECTION.income)
    order = models.IntegerField(default=0)
    deleted_at = models.DateTimeField(null=True)
    group = models.ForeignKey(CategoryGroup, related_name='group_categories', null=True, on_delete=models.SET_NULL)


class CategoryMapping(TimestampedModel):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, related_name='category_mappings', on_delete=models.CASCADE)


class Wallet(TimestampedModel):
    user_id = models.IntegerField()
    name = models.CharField(max_length=255, null=True, blank=True)
    plaid_id = models.IntegerField(null=True)
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


class TransactionByDay(models.Model):
    class Meta:
        managed = False
    user_id = models.IntegerField()
    income_amount = models.DecimalField(max_digits=18, decimal_places=2)
    expense_amount = models.DecimalField(max_digits=18, decimal_places=2)
    transaction_at = models.DateField()
