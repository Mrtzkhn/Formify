from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from accounts.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'phone_number', 'is_active', 'date_joined')
        read_only_fields = ('id', 'is_active', 'date_joined')

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=255)
    phone_number = serializers.CharField(max_length=20, allow_blank=True, required=False)
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        validate_password(value)
        return value

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


# ---- OpenAPI / Schema helpers ----
class TokenPairSerializer(serializers.Serializer):
    """Simple pair of JWT tokens."""
    refresh = serializers.CharField(help_text="JWT refresh token")
    access = serializers.CharField(help_text="JWT access token")

class LogoutRequestSerializer(serializers.Serializer):
    """Request body for logout; the refresh token to blacklist."""
    refresh = serializers.CharField(help_text="Refresh token to blacklist")

