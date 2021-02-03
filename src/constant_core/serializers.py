from rest_framework import serializers

from constant_core.models import UserBank, User


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('user_name', 'full_name', 'email')
        read_only_fields = ('user_name', 'full_name', 'email')
