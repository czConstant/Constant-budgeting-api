import copy
import json
import logging
import time
import traceback

from django.core.serializers.json import DjangoJSONEncoder
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import exception_handler


logger = logging.getLogger('kibana')


class StandardPagination(PageNumberPagination):
    page_size = 100
    max_page_size = 1000
    page_size_query_param = 'page_size'


class SuccessResponse(Response):
    def __init__(self, data=None, code=None, message=None, default_status=None,
                 template_name=None, headers=None,
                 exception=False, content_type=None):
        selected_status = default_status if default_status else status.HTTP_200_OK
        wrapped_data = {
            'code': code if code else 1,
            'message': message if message else "OK",
            'status': selected_status,
            "data": data,
        }
        super(SuccessResponse, self).__init__(wrapped_data, selected_status, template_name, headers, exception,
                                              content_type)


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if response is not None and response.status_code == 400:
        if not type(response.data) is list:
            response.data['status'] = response.status_code
            if 'detail' in response.data:
                response.data['message'] = response.data['detail']
                response.data['code'] = exc.get_codes()
                del response.data['detail']
            else:
                response.data['message'] = 'Validation error'
                response.data['code'] = 'validation_error'
        else:
            response.data = {
                'message': 'Validation error',
                'code': 'validation_error',
                'details': response.data,
            }

    return response


class RequestLogMiddleware(MiddlewareMixin):
    """Request Logging Middleware."""

    SERVICE_URL = '/budgeting-api/'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def process_request(self, request):
        request.traceback = None
        request.error_text = None
        if str(request.get_full_path()).startswith(RequestLogMiddleware.SERVICE_URL):
            request.start_time = time.time()

    def process_exception(self, request, exception):
        request.traceback = traceback.format_exc()
        request.error_text = str(exception)

    def extract_log_info(self, request, response=None, exception=None):
        """Extract appropriate log info from requests/responses/exceptions."""
        request_body = copy.copy(request.body)
        log_data = {
            'ip': request.META.get('HTTP_IP') if request.META.get('HTTP_IP') else request.META['REMOTE_ADDR'],
            'method': request.method,
            'path': request.get_full_path(),
            'latency': time.time() - request.start_time,
            'status': response.status_code if response else 0,
            'service': 'budgeting-api',
            'app_name': 'API_BUGETING',
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'platform': request.META.get('HTTP_PLATFORM'),
            'os': request.META.get('HTTP_OS'),
            'country': request.META.get('HTTP_COUNTRY'),
            'email': request.user.email if request.user and not request.user.is_anonymous else '',
            'user_id': request.user.user_id if request.user and not request.user.is_anonymous else '',
            'body_request': str(request_body)[:1000] if request.POST else '',
            'body_response': response.content.decode('utf-8')[:1000],
            'stacktrace': request.traceback,
            'error_text': request.error_text,

        }
        return log_data

    def process_response(self, request, response):
        """Log data using logger."""
        try:
            if str(request.get_full_path()).startswith(RequestLogMiddleware.SERVICE_URL):
                log_data = self.extract_log_info(request=request,
                                                 response=response)

                log_str = json.dumps(log_data, cls=DjangoJSONEncoder)
                logger.info(log_str)
        except:
            pass

        return response
