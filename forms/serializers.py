
from rest_framework import serializers
from forms.models import Form, FormView, Category, EntityCategory



class FormSerializer(serializers.ModelSerializer):
    view_count = serializers.ReadOnlyField()
    response_count = serializers.ReadOnlyField()
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)

    class Meta:
        model = Form
        fields = [
            'id', 'title', 'description', 'created_by', 'created_by_name',
            'is_public', 'access_password', 'is_active', 'view_count',
            'response_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def validate_access_password(self, value):
        is_public = self.initial_data.get('is_public', True)
        if str(is_public).lower() in ['false', '0'] and not value:
            raise serializers.ValidationError("The password is required for private forms.")
        return value

class FormCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Form
        fields = ['title', 'description', 'is_public', 'access_password']

class FormViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormView
        fields = ['form', 'ip_address', 'user_agent', 'viewed_at']
        read_only_fields = ['viewed_at']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']