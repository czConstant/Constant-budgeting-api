from rest_framework import serializers

from budgeting.models import Category, Transaction, TransactionByDay, Wallet, CategoryGroup


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'code', 'direction', 'description')


class CategoryGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryGroup
        fields = ('name', 'code', 'categories')

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
        fields = ('id', 'name')


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('id', 'transaction_at', 'category',
                  'direction', 'amount', 'wallet', 'note')
        read_only_fields = ('user_id', )
        extra_kwargs = {
            'user_id': {
                'required': False
            },
        }


class TransactionByDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionByDay
        fields = ('income_amount', 'expense_amount', 'transaction_at')
