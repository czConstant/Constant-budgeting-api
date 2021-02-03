from rest_framework import status
from rest_framework.exceptions import APIException


class NotEnoughBalanceException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Not enough balance'
    default_code = 'not_enough_balance'
    balance = 0

    def __init__(self, detail=None, code=None, balance=0):
        super(NotEnoughBalanceException, self).__init__(detail, code)
        self.balance = balance
