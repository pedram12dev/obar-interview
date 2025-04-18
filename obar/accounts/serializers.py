from rest_framework import serializers
from .models import User


class UserCompleteSerializer(serializers.ModelSerializer):
    """
        serialize user objects
    """
    class Meta:
        model = User
        fields = ('email','full_name','password')
        extra_kwargs ={'password':{'write_only':True}}


class PhoneNumberSerializer(serializers.Serializer):
    """
        serialize phone number
    """
    phone_number = serializers.CharField()

