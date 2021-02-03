from rest_framework import status
from rest_framework.exceptions import APIException


class ExternalAPIException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'External API error'
    default_code = 'external_api_error'


class ConstantCoreNotEnoughBalanceException(ExternalAPIException):
    default_detail = 'Not enough balance'
    default_code = 'not_enough_balance'
