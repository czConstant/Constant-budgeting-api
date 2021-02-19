from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from budgeting_auth.authentication import SystemPermission


class ImportPlaidTransactionView(APIView):
    permission_classes = (IsAuthenticated, SystemPermission)

    def post(self, request, format=None):
        return Response()
