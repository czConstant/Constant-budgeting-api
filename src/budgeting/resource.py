from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins

from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet, GenericViewSet

from budgeting.constants import DIRECTION
from budgeting.models import Category, Transaction, Wallet, CategoryGroup
from budgeting.queries import TransactionQueries, WalletQueries
from budgeting.serializers import CategorySerializer, TransactionSerializer, TransactionByDaySerializer, \
    WalletSerializer, CategoryGroupSerializer, WalletBalanceSerializer
from common.http import StandardPagination


class CategoryGroupViewSet(ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    serializer_class = CategoryGroupSerializer
    queryset = CategoryGroup.objects.none()

    def get_queryset(self):
        qs = CategoryGroup.objects.filter(deleted_at__isnull=True).order_by('order')
        return qs

    def list(self, request, *args, **kwargs):
        # Inherited
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        # End

        # Hack serializer
        data = serializer.data
        result = [item for item in data if len(item['categories']) > 0]
        # End

        return Response(result)


class CategoryFilter(filters.FilterSet):
    class Meta:
        model = Category
        fields = ('direction', )

    direction = filters.MultipleChoiceFilter(
        choices=DIRECTION
    )


class CategoryViewSet(ReadOnlyModelViewSet):
    permission_classes = (AllowAny, )
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = CategoryFilter
    serializer_class = CategorySerializer
    queryset = Category.objects.filter(deleted_at__isnull=True).order_by('order')


class WalletViewSet(mixins.CreateModelMixin,
                    mixins.DestroyModelMixin,
                    mixins.ListModelMixin,
                    GenericViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = WalletSerializer
    queryset = Wallet.objects.none()

    def get_queryset(self):
        return Wallet.objects.filter(user_id=self.request.user.user_id,
                                     deleted_at__isnull=True).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        result_list = serializer.data
        for item in result_list:
            item['type'] = 'linked_bank'
        result_list.insert(0, {
            'id': 0,
            'name': 'Total Wallet',
            'type': 'total_wallet'
        })
        return Response(result_list)

    def create(self, request, *args, **kwargs):
        pass

    def destroy(self, request, *args, **kwargs):
        pass

    @action(detail=False, methods=['get'], url_path='balance')
    def balance(self, request):
        qs = WalletQueries.wallet_balance(request.user.user_id)
        data = WalletBalanceSerializer(qs, many=True).data

        return Response(data)


class TransactionFilter(filters.FilterSet):
    class Meta:
        model = Transaction
        fields = {
            'amount': ['exact', 'gt', 'lt', 'gte', 'lte']
        }

    direction = filters.MultipleChoiceFilter(
        choices=DIRECTION
    )
    from_date = filters.DateFilter(field_name='transaction_at', lookup_expr='gte')
    to_date = filters.DateFilter(field_name='transaction_at', lookup_expr='lte')


class TransactionViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = TransactionFilter
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.none()
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = Transaction.objects.filter(user_id=self.request.user.user_id).order_by('-created_at')
        wallet_id = self.request.query_params.get('wallet')
        if wallet_id == '0':
            qs = qs.filter(wallet__isnull=True)
        else:
            qs = qs.filter(wallet_id=wallet_id)

        return qs
    
    def create(self, request, *args, **kwargs):
        wallet_id = request.data.get('wallet')
        if wallet_id is not None and int(wallet_id) == 0:
            request.data.pop('wallet')

        return super(TransactionViewSet, self).create(request, *args, **kwargs)

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
        wallet_id = request.query_params.get('wallet')
        if not month:
            raise ValidationError('month is required as format YY-MMMM')

        qs = TransactionQueries.get_transaction_by_month(request.user.user_id, month, wallet_id=wallet_id)
        data = TransactionByDaySerializer(qs, many=True).data

        return Response(data)

    @action(detail=False, methods=['get'], url_path='month-summary')
    def month_summary(self, request):
        # Format: 2021-02
        month = request.query_params.get('month')
        wallet_id = request.query_params.get('wallet')
        if not month:
            raise ValidationError('month is required as format YY-MMMM')

        data = TransactionQueries.get_transaction_month_summary(request.user.user_id, month, wallet_id=wallet_id)

        return Response(data)
