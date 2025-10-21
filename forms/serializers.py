
from rest_framework import serializers
from django.core.exceptions import ValidationError
from forms.models import Form, FormView, Category, EntityCategory, Field



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


class FieldSerializer(serializers.ModelSerializer):
    """Serializer for displaying field data."""
    field_type_display = serializers.CharField(source='get_field_type_display', read_only=True)
    form_title = serializers.CharField(source='form.title', read_only=True)
    
    class Meta:
        model = Field
        fields = [
            'id', 'form', 'form_title', 'label', 'field_type', 'field_type_display',
            'is_required', 'options', 'order_num', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FieldCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new fields."""
    
    class Meta:
        model = Field
        fields = ['form', 'label', 'field_type', 'is_required', 'options', 'order_num']
    
    def validate_options(self, value):
        """Validate field options based on field type."""
        field_type = self.initial_data.get('field_type')
        if not field_type:
            return value
        
        # Import here to avoid circular imports
        from forms.services.services import FieldService
        
        try:
            FieldService.validate_field_options(field_type, value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        
        return value
    
    def validate_form(self, value):
        """Ensure user owns the form."""
        user = self.context['request'].user
        if value.created_by != user:
            raise serializers.ValidationError("You can only add fields to your own forms.")
        return value


class FieldUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating existing fields."""
    
    class Meta:
        model = Field
        fields = ['label', 'field_type', 'is_required', 'options', 'order_num']
    
    def validate_options(self, value):
        """Validate field options based on field type."""
        field_type = self.initial_data.get('field_type', self.instance.field_type if self.instance else None)
        if not field_type:
            return value
        
        # Import here to avoid circular imports
        from forms.services.services import FieldService
        
        try:
            FieldService.validate_field_options(field_type, value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        
        return value


class FieldListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for field lists."""
    field_type_display = serializers.CharField(source='get_field_type_display', read_only=True)
    
    class Meta:
        model = Field
        fields = ['id', 'label', 'field_type', 'field_type_display', 'is_required', 'order_num']


class FieldReorderSerializer(serializers.Serializer):
    """Serializer for field reordering."""
    new_order = serializers.IntegerField(min_value=1)
    
    def validate_new_order(self, value):
        """Validate the new order number."""
        field = self.context['field']
        max_order = Field.objects.filter(form=field.form).count()
        
        if value > max_order:
            raise serializers.ValidationError(f"Order number cannot exceed {max_order}.")
        
        return value