import json

from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.business import get_now
from budgeting_auth.authentication import SystemPermission
from budgeting_pubsub.constants import SUB_LOG_STATUS
from budgeting_pubsub.google_pubsub import PubSub
from budgeting_pubsub.models import SubLog


class HandleSubView(APIView):
    permission_classes = (IsAuthenticated, SystemPermission)

    def post(self, request, message_id, format=None):
        obj = SubLog.objects.filter(task=self.get_task(), message_id=message_id).order_by('-id').last()

        try:
            data = self.run_post(request)
            obj.status = SUB_LOG_STATUS.success
        except Exception as ex:
            data = {'error': str(ex)}
            obj.status = SUB_LOG_STATUS.failed

        obj.response = json.dumps(data, cls=DjangoJSONEncoder)
        obj.save()

        return Response({'status': 'ok'})

    def get_task(self):
        return 'base'

    def run_post(self, request):
        return {}


class SubView(APIView):
    permission_classes = (IsAuthenticated, SystemPermission)

    def post(self, request, format=None):
        PubSub.async_receive_message_exchange()

        return Response({'status': 'ok'})


class TestTaskView(HandleSubView):
    def get_task(self):
        return 'test'

    def run_post(self, request):
        return {'task': 'received {}'.format(get_now())}
