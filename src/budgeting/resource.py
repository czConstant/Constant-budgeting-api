from datetime import date, timedelta

from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status

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
    WalletSerializer, CategoryGroupSerializer, WalletBalanceSerializer, TransactionLinkedBankSerializer
from common.business import get_now
from common.http import StandardPagination
from constant_core.business import ConstantCoreBusiness


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

    def check_object_permissions(self, request, obj):
        super(WalletViewSet, self).check_object_permissions(request, obj)
        if not request.user.user_id == obj.user_id:
            self.permission_denied(request)

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
        plaid_id = request.data.get('plaid_id')
        if not plaid_id:
            raise ValidationError('plaid_id is required')
        plaid = ConstantCoreBusiness.get_plaid_account(plaid_id)
        if not plaid:
            raise ValidationError('Invalid plaid_id')

        wallet = Wallet.objects.filter(user_id=request.user.user_id, plaid_id=plaid.id).first()
        if wallet:
            if wallet.deleted_at:
                wallet.deleted_at = None
                wallet.last_import = date.today()
            wallet.save()
        else:
            last_day_of_prev_month = date.today().replace(day=1) - timedelta(days=1)
            start_day_of_prev_month = date.today().replace(day=1) - timedelta(days=last_day_of_prev_month.day)
            wallet = Wallet.objects.create(
                user_id=request.user.user_id,
                plaid_id=plaid.id,
                name=plaid.plaid_name,
                last_import=start_day_of_prev_month,
            )

        serializer = WalletSerializer(wallet)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deleted_at = get_now()
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

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
        qs = Transaction.objects.filter(user_id=self.request.user.user_id,
                                        wallet__deleted_at__isnull=True)
        wallet_id = self.request.query_params.get('wallet')
        if wallet_id is not None:
            if wallet_id == '0':
                qs = qs.filter(wallet__isnull=True)
            else:
                qs = qs.filter(wallet_id=wallet_id)

        qs = qs.order_by('-created_at')

        return qs

    def check_object_permissions(self, request, obj):
        super(TransactionViewSet, self).check_object_permissions(request, obj)
        if not request.user.user_id == obj.user_id:
            self.permission_denied(request)

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.user_id)

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()

        # Edit linked bank transaction
        if args and isinstance(args[0], Transaction) and args[0].wallet_id is not None:
            serializer_class = TransactionLinkedBankSerializer

        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.wallet_id is None:
            self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

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
