from decimal import Decimal

from django.db import models
from django.utils import timezone


class ConstantManager(models.Manager):
    def get_queryset(self):
        return models.QuerySet(self.model, using='constant')


class ConstantReadManager(models.Manager):
    def get_queryset(self):
        return models.QuerySet(self.model, using='constant_read')


class UserBankManager(ConstantManager):
    def available(self):
        return self.filter(deleted_at__isnull=True)


class User(models.Model):
    class Meta:
        db_table = 'users'
        managed = False

    id = models.PositiveIntegerField(primary_key=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    user_name = models.CharField(max_length=255, blank=True)
    full_name = models.CharField(max_length=255, blank=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    middle_name = models.CharField(max_length=255, blank=True)
    email = models.CharField(max_length=255)
    constant_balance = models.BigIntegerField(default=0)
    constant_balance_holding = models.BigIntegerField(default=0)
    pro_saving_user = models.BooleanField(default=False)
    agent_user = models.BooleanField(default=False)
    lo_user = models.BooleanField(default=False)
    dob = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=255, blank=True)
    address_country = models.CharField(max_length=255, blank=True)
    tax_country = models.CharField(max_length=255, blank=True)

    status = models.IntegerField(default=1)
    user_role_id = models.IntegerField(default=0)
    type = models.IntegerField(default=0)
    verified_level = models.IntegerField(default=0)
    account_type = models.IntegerField(default=0)
    gender = models.IntegerField(default=1)
    primetrust_contact_status = models.IntegerField(default=-1)
    referral_code = models.CharField(max_length=255, blank=True)
    social_type = models.IntegerField(default=0)
    is_reset_password = models.IntegerField(default=0)
    is_first_reset_password = models.IntegerField(default=0)
    reset_password_token = models.CharField(max_length=255)
    api_token = models.CharField(max_length=255)
    language = models.CharField(max_length=255)
    white_label = models.BooleanField(default=False)
    permissions = models.TextField(null=True, blank=True)
    membership = models.IntegerField(default=0)
    is_skip_check_balance = models.BooleanField(default=False)
    device_token = models.CharField(max_length=255)
    withdraw_confirmed_email_on = models.BooleanField()
    suspend_withdrawal_to = models.DateTimeField()

    objects = ConstantManager()

    @property
    def constant_balance_friendly(self):
        return self.constant_balance / Decimal(100)

    @property
    def constant_balance_holding_friendly(self):
        return self.constant_balance_holding / Decimal(100)

    @property
    def is_kyc(self):
        return self.verified_level in (6, 7)

    @property
    def user_id(self):
        return self.id

    @property
    def internal_user(self):
        return self.account_type == 2

    def build_dict(self):
        return {
            'full_name': self.full_name,
            'email': self.email,
            'balance': '{:.2f}'.format(self.constant_balance_friendly)
        }


class UserExtraInfo(models.Model):
    class Meta:
        db_table = 'user_extra_infos'
        managed = False

    user_id = models.PositiveIntegerField()
    last_withdraw = models.DateTimeField()

    objects = ConstantManager()


class Reserves(models.Model):
    class Meta:
        db_table = 'reserves'
        managed = False

    RESERVE_TYPE_TRANSFER = 2
    RESERVE_TYPE_TERM_DEPOSIT = 3
    RESERVE_TYPE_INTEREST = 4
    RESERVE_TYPE_FEE = 5
    RESERVE_TYPE_DEPOSIT = 7
    RESERVE_TYPE_WITHDRAW = 8
    RESERVE_TYPE_RISK = 9

    RESERVE_STATUS_CANCELLED = 6
    RESERVE_STATUS_DONE = 7
    RESERVE_STATUS_HOLDING = 8

    RESERVE_STATUS_EMAIL_CONFIRMING = 15
    RESERVE_STATUS_EMAIL_TIMEOUT = 16

    id = models.AutoField(primary_key=True)
    user_id = models.PositiveIntegerField()
    status = models.PositiveSmallIntegerField(default=7)
    payment_status = models.PositiveSmallIntegerField(default=0)
    reserve_type = models.PositiveSmallIntegerField(default=RESERVE_TYPE_TRANSFER)
    amount = models.BigIntegerField()
    fee = models.BigIntegerField(default=0)
    tx_hash = models.CharField(max_length=10, blank=True)
    wallet_address = models.CharField(max_length=10, blank=True)
    to_user_id = models.PositiveIntegerField()
    ext_request = models.CharField(max_length=10, blank=True)
    ext_response = models.TextField(blank=True)
    ext_error = models.CharField(max_length=10, blank=True)
    ext_id = models.CharField(max_length=255, blank=True)
    ref_id = models.PositiveIntegerField()
    ext_status = models.CharField(max_length=10, blank=True)
    reference = models.CharField(max_length=255, blank=True)
    token = models.CharField(max_length=255, blank=True, null=True)
    token_expired_at = models.DateTimeField(null=True)
    parent = models.ForeignKey('Reserves', related_name='parent_reserves', null=True, on_delete=models.PROTECT)
    admin_note = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ConstantManager()


class UserTx:
    HoldConstantBalance = 0
    ReleaseConstantBalance = 1
    IncreaseConstantBalance = 2
    DecreaseConstantBalance = 3
    IncreaseConstantBalanceHolding = 4
    DecreaseConstantBalanceHolding = 5
    TransferConstantBalance = 6
    TransferConstantBalanceWithFromHolding = 7
    TransferConstantBalanceWithToHolding = 8


class AdminLogActions(models.Model):
    class Meta:
        db_table = 'admin_log_actions'
        managed = False

    objects = ConstantManager()

    id = models.AutoField(primary_key=True)
    user_id = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    request_url = models.CharField(max_length=255, blank=True)
    request_body = models.CharField(max_length=255, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    proto = models.CharField(max_length=255, blank=True)
    referer = models.CharField(max_length=255, blank=True)
    client_ip = models.CharField(max_length=255, blank=True)
    response = models.TextField(blank=True)
    method = models.CharField(max_length=255, blank=True)


class PlaidAccounts(models.Model):
    class Meta:
        db_table = 'plaid_accounts'
        managed = False

    objects = ConstantManager()

    id = models.AutoField(primary_key=True)
    user_id = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True)
    access_token = models.CharField(max_length=255)
    institution_name = models.CharField(max_length=255)
    account_subtype = models.CharField(max_length=255)
    is_default = models.BooleanField()

    @property
    def plaid_name(self):
        return '{} ({})'.format(self.institution_name, self.account_subtype)

class AdminPages(models.Model):
    class Meta:
        db_table = 'admin_pages'
        managed = False

    objects = ConstantManager()
    read_objects = ConstantReadManager()

    name = models.CharField(max_length=255)


class AdminPermissions(models.Model):
    class Meta:
        db_table = 'admin_permissions'
        managed = False

    objects = ConstantManager()
    read_objects = ConstantReadManager()

    page_id = models.IntegerField()
    group_id = models.IntegerField()
    can_view = models.BooleanField()
    can_add = models.BooleanField()
    can_update = models.BooleanField()
    can_delete = models.BooleanField()


class AdminUserGroups(models.Model):
    class Meta:
        db_table = 'admin_user_groups'
        managed = False

    objects = ConstantManager()
    read_objects = ConstantReadManager()

    group_id = models.IntegerField()
    user_id = models.IntegerField()
