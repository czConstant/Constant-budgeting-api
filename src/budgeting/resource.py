from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from budgeting.models import Category, Transaction
from budgeting.queries import TransactionQueries
from budgeting.serializers import CategorySerializer, TransactionSerializer, TransactionByDaySerializer
from common.http import StandardPagination


class CategoryViewSet(ReadOnlyModelViewSet):
    permission_classes = (AllowAny, )
    serializer_class = CategorySerializer
    queryset = Category.objects.filter(deleted_at__isnull=True).order_by('order')
    pagination_class = StandardPagination


class TransactionViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.none()
    pagination_class = StandardPagination

    def get_queryset(self):
        return Transaction.objects.filter(user_id=self.request.user.user_id).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.user_id)

    @action(detail=False, methods=['get'], url_path='by-month')
    def by_month(self, request):
        # Format: 2021-02
        month = request.query_params.get('month')
        qs = TransactionQueries.get_transaction_by_month(request.user.user_id, month)
        data = TransactionByDaySerializer(qs, many=True).data

        return Response(data)
