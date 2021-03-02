import logging
import traceback

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from budgeting.business.notification import BudgetingNotification
from budgeting.business.transaction import TransactionBusiness
from budgeting.constants import TASK_NOTE
from budgeting.models import Wallet, TaskNote
from budgeting_auth.authentication import SystemPermission
from common.business import get_now


class StartView(APIView):
    def get(self, request, format=None):
        return Response('API works')


class ImportPlaidTransactionView(APIView):
    permission_classes = (IsAuthenticated, SystemPermission)

    def post(self, request, format=None):
        wallets = Wallet.objects.filter(plaid_id__isnull=False,
                                        deleted_at__isnull=True,
                                        last_import__lt=get_now().today())
        count = 0
        success_count = 0
        failed_count = 0
        for wallet in wallets:
            try:
                from_dt = wallet.last_import
                to_dt = get_now().today()
                TransactionBusiness.import_transaction_from_plaid(wallet.user_id, wallet, from_dt, to_dt)
                wallet.last_import = to_dt
                wallet.error = wallet.error_details = wallet.error_at = None
                wallet.save()
                success_count += 1

                try:
                    tn = TaskNote.objects.filter(user_id=wallet.user_id,
                                                 task=TASK_NOTE.first_import_transaction_notification,
                                                 obj_id=wallet.id).first()
                    if not tn:
                        BudgetingNotification.noti_transaction_imported(wallet.user_id)
                        TaskNote.objects.create(user_id=wallet.user_id,
                                                task=TASK_NOTE.first_import_transaction_notification,
                                                obj_id=wallet.id,
                                                count=1)
                except Exception as noti_ex:
                    logging.exception(noti_ex)
            except Exception as ex:
                wallet.error = str(ex)
                wallet.error_details = traceback.format_exc()
                wallet.error_at = get_now()
                wallet.save()
                failed_count += 1

            count += 1
            # Ten at a time
            if count == 10:
                break

        return Response({
            'success': success_count,
            'failed': failed_count,
        })
