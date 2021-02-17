from rest_framework import serializers

from budgeting.models import Category, Transaction, TransactionByDay


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'description')


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ('user_id', )
        extra_kwargs = {
            'user_id': {
                'required': False
            },
        }


class TransactionByDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionByDay
        fields = ('income_amount', 'expense_amount', 'created_at')
