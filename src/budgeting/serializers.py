from rest_framework import serializers

from budgeting.business.category import CategoryBusiness
from budgeting.models import Category, Transaction, TransactionByDay, Wallet, CategoryGroup, WalletBalance, \
    TransactionByCategory


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'code', 'direction', 'description', 'user_id')


class WriteCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'direction', 'description', 'group')
        kwargs = {
            'group': {
                'required': True
            }
        }

    def validate(self, attrs):
        attrs['user_id'] = self.context['request'].user.user_id
        attrs['code'] = Category.MANUAL_CODE
        return attrs


class CategoryGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryGroup
        fields = ('id', 'name', 'code', 'categories')

    categories = serializers.SerializerMethodField()

    def get_categories(self, instance):
        qs = instance.group_categories.filter(deleted_at__isnull=True)
        if 'request' in self.context:
            direction = self.context['request'].query_params.get('direction')
            if direction:
                qs = qs.filter(direction=direction)
        qs = qs.order_by('order')
        serializer = CategorySerializer(qs, many=True, context=self.context)
        return serializer.data


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ('id', 'name', 'sub_name', 'plaid_id')


class WalletBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletBalance
        fields = '__all__'


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('id', 'transaction_at', 'category', 'category_name', 'category_code',
                  'direction', 'amount', 'wallet', 'wallet_id', 'note',
                  'location', 'location_name')
        read_only_fields = ('wallet', )

    wallet_id = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    category_code = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    location_name = serializers.SerializerMethodField()

    def get_wallet_id(self, instance):
        return instance.wallet_id if instance.wallet_id else 0

    def get_category_detail(self, instance):
        category = instance.category
        if not category:
            category = CategoryBusiness.default_category(instance.direction)

        return {
            'code': category.code if category else Category.DEFAULT_CODE,
            'name': category.name if category else 'Others'
        }

    def get_category_code(self, instance):
        return self.get_category_detail(instance)['code']

    def get_category_name(self, instance):
        return self.get_category_detail(instance)['name']

    def get_location_name(self, instance):
        return instance.detail_dict.get('location_name')

    def get_location(self, instance):
        return instance.detail_dict.get('location')

    def validate(self, attrs):
        if 'category' not in attrs:
            cat = Category.objects.filter(code='others', direction=attrs['direction']).first()
            attrs['category'] = cat

        return attrs


class TransactionLinkedBankSerializer(TransactionSerializer):
    class Meta:
        model = Transaction
        fields = ('id', 'transaction_at', 'category',
                  'direction', 'amount', 'wallet', 'wallet_id', 'note')
        read_only_fields = ('transaction_at', 'direction', 'amount', 'wallet')


class TransactionByDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionByDay
        fields = ('income_amount', 'expense_amount', 'transaction_at')


class TransactionByCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionByCategory
        fields = ('category_id', 'category_code', 'category_name', 'amount')
