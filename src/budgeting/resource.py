from datetime import date, timedelta

from django.db.models import Q
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status

from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet, GenericViewSet

from budgeting.business.category import CategoryBusiness
from budgeting.business.wallet import WalletBusiness
from budgeting.constants import DIRECTION
from budgeting.models import Category, Transaction, Wallet, CategoryGroup, Budget
from budgeting.queries import TransactionQueries, WalletQueries, BudgetQueries
from budgeting.serializers import CategorySerializer, TransactionSerializer, TransactionByDaySerializer, \
    WalletSerializer, CategoryGroupSerializer, WalletBalanceSerializer, TransactionLinkedBankSerializer, \
    WriteCategorySerializer, TransactionByCategorySerializer, BudgetSerializer, BudgetDetailSerializer
from common.business import get_now
from common.http import StandardPagination
from constant_core.business import ConstantCoreBusiness


class CategoryGroupViewSet(ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)
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


class CategoryViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated, )
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = CategoryFilter
    serializer_class = CategorySerializer
    queryset = Category.objects.filter(deleted_at__isnull=True).order_by('order')

    def check_object_permissions(self, request, obj):
        super(CategoryViewSet, self).check_object_permissions(request, obj)
        if (not obj.user_id) or (obj.user_id and request.user.user_id != obj.user_id):
            self.permission_denied(request)

    def get_serializer_class(self):
        if self.request.method != 'GET':
            return WriteCategorySerializer
        return CategorySerializer

    def perform_destroy(self, instance):
        CategoryBusiness.remove_user_category(instance)


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
            'name': 'Manual Wallet',
            'type': 'manual_wallet'
        })
        return Response(result_list)

    def create(self, request, *args, **kwargs):
        plaid_id = request.data.get('plaid_id')
        if not plaid_id:
            raise ValidationError('plaid_id is required')

        wallet = WalletBusiness.add_wallet(request.user, plaid_id)

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
            'amount': ['exact', 'gt', 'lt', 'gte', 'lte'],
        }

    direction = filters.MultipleChoiceFilter(
        choices=DIRECTION
    )
    from_date = filters.DateFilter(field_name='transaction_at', lookup_expr='gte')
    to_date = filters.DateFilter(field_name='transaction_at', lookup_expr='lt')


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
        wallet_id = self.request.query_params.get('wallet_id')
        if wallet_id is not None:
            if wallet_id == '0':
                qs = qs.filter(wallet__isnull=True)
            else:
                qs = qs.filter(wallet_id=wallet_id)
        cat_id = self.request.query_params.get('category_id')
        if cat_id is not None:
            cat = Category.objects.filter(id=cat_id).first()
            if cat:
                if cat.code == Category.DEFAULT_CODE:
                    qs = qs.filter(Q(category=cat) | Q(category__isnull=True), direction=cat.direction)
                else:
                    qs = qs.filter(category=cat)

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
            raise ValidationError('month is required as format YYYY-MM')

        data = TransactionQueries.get_transaction_summary(request.user.user_id, 'month', month, wallet_id=wallet_id)

        return Response(data)

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        # Format: 2021-02 / 2021
        dt = request.query_params.get('range')
        wallet_id = request.query_params.get('wallet')
        t = request.query_params.get('type', 'month')
        if t not in ('year', 'month'):
            raise ValidationError('Invalid type. Possible values: year|month')
        if not dt:
            raise ValidationError('range is required as format YYYY|YYYY-MM')

        data = TransactionQueries.get_transaction_summary(request.user.user_id, t, dt, wallet_id=wallet_id)

        return Response(data)

    @action(detail=False, methods=['get'], url_path='summary-by-category')
    def summary_by_category(self, request):
        # Format: 2021-02 / 2021
        dt = request.query_params.get('range')
        wallet_id = request.query_params.get('wallet')
        t = request.query_params.get('type', 'month')
        direction = request.query_params.get('direction')
        if t not in ('year', 'month'):
            raise ValidationError('Invalid type. Possible values: year|month')
        if not dt:
            raise ValidationError('range is required as format YYYY|YYYY-MM')
        if direction not in (DIRECTION.income, DIRECTION.expense):
            raise ValidationError('Invalid direction. Possible value: income|expense')

        qs = TransactionQueries.get_transaction_summary_by_category(
            request.user.user_id, t, direction, dt, wallet_id=wallet_id)
        data = TransactionByCategorySerializer(qs, many=True).data

        return Response(data)

    @action(detail=False, methods=['get'], url_path='summary-category-by-month')
    def summary_category_by_month(self, request):
        # Format: 2021-02
        from_month = request.query_params.get('from_month')
        to_month = request.query_params.get('to_month')
        wallet_id = request.query_params.get('wallet')
        category_id = request.query_params.get('category_id')
        if not category_id:
            raise ValidationError('category_id is required')

        data = TransactionQueries.get_transaction_summary_category_by_month(
            request.user.user_id, category_id, from_month, to_month, wallet_id=wallet_id)

        return Response(data)


class TransactionNoPagingViewSet(TransactionViewSet):
    pagination_class = None


class BudgetViewSet(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = BudgetSerializer
    queryset = Budget.objects.none()

    def get_queryset(self):
        qs = Budget.objects.filter(user_id=self.request.user.user_id)
        qs = qs.order_by('-id')
        return qs

    def check_object_permissions(self, request, obj):
        super(BudgetViewSet, self).check_object_permissions(request, obj)
        if not request.user.user_id == obj.user_id:
            self.permission_denied(request)

    def list(self, request, *args, **kwargs):
        user_id = request.user.user_id
        wallet_id = request.query_params.get('wallet_id')
        if not wallet_id:
            raise ValidationError('wallet_id is required')
        is_end = request.query_params.get('is_end')
        is_over = request.query_params.get('is_over')

        qs = BudgetQueries.get_budget_details(user_id, wallet_id, is_end, is_over)
        serializer = BudgetDetailSerializer(qs, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.request.method != 'GET':
            return BudgetSerializer
        return BudgetDetailSerializer

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.user_id)
