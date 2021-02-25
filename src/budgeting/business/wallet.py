from datetime import date, timedelta

from rest_framework.exceptions import ValidationError

from budgeting.models import Wallet, ConstUser
from constant_core.business import ConstantCoreBusiness


class WalletBusiness:
    @staticmethod
    def add_wallet(user: ConstUser, plaid_id: int):
        plaid = ConstantCoreBusiness.get_plaid_account(plaid_id)
        if not plaid:
            raise ValidationError('Invalid plaid_id')

        wallet = Wallet.objects.filter(user_id=user.user_id, plaid_id=plaid.id).first()
        if wallet:
            if wallet.deleted_at:
                wallet.deleted_at = None
                wallet.last_import = date.today()
            wallet.save()
        else:
            last_day_of_prev_month = date.today().replace(day=1) - timedelta(days=1)
            start_day_of_prev_month = date.today().replace(day=1) - timedelta(days=last_day_of_prev_month.day)
            wallet = Wallet.objects.create(
                user_id=user.user_id,
                plaid_id=plaid.id,
                name=plaid.institution_name,
                sub_name=plaid.account_subtype,
                last_import=start_day_of_prev_month,
            )

        return wallet
