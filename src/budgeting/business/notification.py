from budgeting.constants import NOTIFICATION_TYPE
from constant_core.business import ConstantCoreBusiness
from integration_3rdparty.const_hook import ConstantHookManagement


class BudgetingNotification:
    @staticmethod
    def noti_transaction_imported(user_id, data=None):
        data['user_id'] = user_id
        data['type'] = NOTIFICATION_TYPE.transaction_imported
        data['player_ids'] = ConstantCoreBusiness.get_device_tokens([user_id])
        ConstantHookManagement.send_notification(data)

    @staticmethod
    def noti_budget_end(user_id, data=None):
        data['user_id'] = user_id
        data['type'] = NOTIFICATION_TYPE.budget_end
        data['player_ids'] = ConstantCoreBusiness.get_device_tokens([user_id])
        ConstantHookManagement.send_notification(data)

    @staticmethod
    def noti_budget_over(user_id, data=None):
        data['user_id'] = user_id
        data['type'] = NOTIFICATION_TYPE.budget_over
        data['player_ids'] = ConstantCoreBusiness.get_device_tokens([user_id])
        ConstantHookManagement.send_notification(data)
