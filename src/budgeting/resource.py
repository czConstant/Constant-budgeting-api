from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from budgeting.models import Category, Transaction
from budgeting.serializers import CategorySerializer, TransactionSerializer
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
