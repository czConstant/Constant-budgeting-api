from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from budgeting.constants import DIRECTION
from budgeting.models import Category, Transaction
from budgeting.queries import TransactionQueries
from budgeting.serializers import CategorySerializer, TransactionSerializer, TransactionByDaySerializer
from common.http import StandardPagination


class CategoryViewSet(ReadOnlyModelViewSet):
    permission_classes = (AllowAny, )
    serializer_class = CategorySerializer
    queryset = Category.objects.filter(deleted_at__isnull=True).order_by('order')


class TransactionFilter(filters.FilterSet):
    class Meta:
        model = Transaction
        fields = {
            'amount': ['exact', 'gt', 'lt', 'gte', 'lte']
        }

    direction = filters.MultipleChoiceFilter(
        choices=DIRECTION
    )
    from_date = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    to_date = filters.DateFilter(field_name='created_at', lookup_expr='lte')


class TransactionViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = TransactionFilter
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.none()
    pagination_class = StandardPagination

    def get_queryset(self):
        return Transaction.objects.filter(user_id=self.request.user.user_id).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.user_id)

    def check_object_permissions(self, request, obj):
        super(TransactionViewSet, self).check_object_permissions(request, obj)
        if not request.user.user_id == obj.user_id:
            self.permission_denied(request)

    @action(detail=False, methods=['get'], url_path='by-month')
    def by_month(self, request):
        # Format: 2021-02
        month = request.query_params.get('month')
        qs = TransactionQueries.get_transaction_by_month(request.user.user_id, month)
        data = TransactionByDaySerializer(qs, many=True).data

        return Response(data)
