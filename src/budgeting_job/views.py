from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from budgeting_auth.authentication import SystemPermission


class ImportPlaidTransactionView(APIView):
    permission_classes = (IsAuthenticated, SystemPermission)

    def post(self, request, format=None):
        return Response()


from budgeting.business.transaction import TransactionBusiness
from budgeting.models import Wallet
from datetime import datetime

def do_import():
    from_dt = datetime(2021, 2, 1)
    to_dt = datetime(2021, 2, 22)
    wallet = Wallet.objects.filter(user_id=800).first()
    TransactionBusiness.import_transaction_from_plaid(800, wallet, from_dt, to_dt)
